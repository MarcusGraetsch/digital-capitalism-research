#!/usr/bin/env python3
"""
RSS Feed Scanner - Fetch articles from configured RSS feeds.
Reads feed list from news-digest-config-v2.json and inserts new articles
into the same articles.db used by the email scanner pipeline.
"""

import os
import re
import json
import sqlite3
import hashlib
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse
from xml.etree import ElementTree
from bs4 import BeautifulSoup

RESEARCH_DIR = Path(os.environ.get('RESEARCH_DIR', '/root/.openclaw/workspace/research'))
WORKSPACE = RESEARCH_DIR.parent
CONFIG_FILE = WORKSPACE / 'news-digest-config-v2.json'
DB_FILE = RESEARCH_DIR / 'articles.db'
FULLTEXT_DIR = RESEARCH_DIR / 'fulltext'
LOG_FILE = RESEARCH_DIR / 'scan_rss.log'
STATE_FILE = RESEARCH_DIR / 'rss_state.json'
REQUEST_DELAY = 1.5
# Only fetch articles from the last N days
MAX_AGE_DAYS = 14


def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def load_config():
    """Load feed configuration"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_state():
    """Load RSS scan state (last seen article IDs per feed)"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def generate_id(url):
    return hashlib.md5(url.encode()).hexdigest()


def url_exists(url):
    """Check if URL already in database"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM articles WHERE url = ?', (url,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def parse_feed(feed_url):
    """Parse an RSS/Atom feed and return list of entries"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)',
            'Accept': 'application/rss+xml, application/xml, text/xml',
        }
        resp = requests.get(feed_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            return [], f"HTTP {resp.status_code}"

        root = ElementTree.fromstring(resp.content)

        entries = []

        # RSS 2.0 format
        for item in root.iter('item'):
            entry = _parse_rss_item(item)
            if entry:
                entries.append(entry)

        # Atom format
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for item in root.findall('.//atom:entry', ns):
            entry = _parse_atom_entry(item, ns)
            if entry:
                entries.append(entry)

        # Also try without namespace (some feeds)
        if not entries:
            for item in root.iter('entry'):
                entry = _parse_atom_entry_no_ns(item)
                if entry:
                    entries.append(entry)

        return entries, None

    except ElementTree.ParseError as e:
        return [], f"XML parse error: {e}"
    except requests.RequestException as e:
        return [], f"Request failed: {e}"
    except Exception as e:
        return [], str(e)


def _parse_rss_item(item):
    """Parse a single RSS <item>"""
    link = _get_text(item, 'link')
    if not link:
        return None

    return {
        'url': link.strip(),
        'title': _get_text(item, 'title') or 'Untitled',
        'description': _get_text(item, 'description') or '',
        'pub_date': _get_text(item, 'pubDate'),
        'author': _get_text(item, 'author') or _get_text(item, '{http://purl.org/dc/elements/1.1/}creator'),
    }


def _parse_atom_entry(item, ns):
    """Parse a single Atom <entry>"""
    link_el = item.find('atom:link[@rel="alternate"]', ns)
    if link_el is None:
        link_el = item.find('atom:link', ns)
    if link_el is None:
        return None

    url = link_el.get('href', '').strip()
    if not url:
        return None

    return {
        'url': url,
        'title': _get_text_ns(item, 'atom:title', ns) or 'Untitled',
        'description': _get_text_ns(item, 'atom:summary', ns) or _get_text_ns(item, 'atom:content', ns) or '',
        'pub_date': _get_text_ns(item, 'atom:published', ns) or _get_text_ns(item, 'atom:updated', ns),
        'author': None,
    }


def _parse_atom_entry_no_ns(item):
    """Parse Atom entry without namespace"""
    link_el = item.find('link[@rel="alternate"]')
    if link_el is None:
        link_el = item.find('link')
    if link_el is None:
        return None

    url = link_el.get('href', '').strip()
    if not url:
        return None

    return {
        'url': url,
        'title': _get_text(item, 'title') or 'Untitled',
        'description': _get_text(item, 'summary') or _get_text(item, 'content') or '',
        'pub_date': _get_text(item, 'published') or _get_text(item, 'updated'),
        'author': None,
    }


def _get_text(element, tag):
    el = element.find(tag)
    return el.text.strip() if el is not None and el.text else None


def _get_text_ns(element, tag, ns):
    el = element.find(tag, ns)
    return el.text.strip() if el is not None and el.text else None


def fetch_article(url):
    """Fetch full article content from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            return {'error': f'HTTP {resp.status_code}', 'http_status': resp.status_code}

        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        title = soup.find('title')
        title = title.get_text(strip=True) if title else 'Unknown'

        author = None
        author_meta = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', property='article:author')
        if author_meta:
            author = author_meta.get('content')

        article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile('content|article'))
        if article:
            text = article.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n\n'.join(lines)

        paywall_indicators = [
            'subscribe', 'premium', 'paywall', 'login to read',
            'register to continue', 'bitte anmelden', 'abonnieren'
        ]
        has_paywall = any(ind in text.lower()[:3000] for ind in paywall_indicators)

        return {
            'title': title,
            'text': text,
            'author': author,
            'word_count': len(text.split()),
            'paywall': has_paywall,
            'http_status': resp.status_code,
        }
    except requests.RequestException as e:
        return {'error': str(e), 'http_status': None}
    except Exception as e:
        return {'error': str(e), 'http_status': None}


def save_fulltext(url, content, category):
    """Save article fulltext to markdown file"""
    now = datetime.now()
    dir_path = FULLTEXT_DIR / now.strftime('%Y-%m')
    dir_path.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    domain = urlparse(url).netloc.replace('www.', '')
    filename = f"{url_hash}_{domain}.md"
    file_path = dir_path / filename

    header = f"""---
url: {url}
title: {content.get('title', 'Unknown')}
domain: {domain}
category: {category}
source: rss
date_scanned: {now.isoformat()}
word_count: {content.get('word_count', 0)}
paywall: {content.get('paywall', False)}
---

# {content.get('title', 'Unknown')}

**URL:** {url}

**Domain:** {domain}

**Category:** {category}

**Source:** RSS Feed

**Scanned:** {now.isoformat()}

**Word Count:** {content.get('word_count', 0)}

---

{content.get('text', '')}
"""

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(header)

    return str(file_path)


def insert_article(url, content, feed_name, category, feed_priority):
    """Insert article into database"""
    conn = sqlite3.connect(DB_FILE)
    try:
        article_id = generate_id(url)
        domain = urlparse(url).netloc.replace('www.', '')
        now = datetime.now().isoformat()

        fulltext_path = save_fulltext(url, content, category)
        text = content.get('text', '')
        abstract = text[:500] + '...' if len(text) > 500 else text

        # Compute content hash
        words = text.split()[:500]
        content_hash = hashlib.md5(' '.join(w.lower() for w in words).encode()).hexdigest() if words else None

        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO articles (
                id, url, domain, title, author, access_date,
                email_account, email_subject, content_status,
                fulltext_path, abstract, word_count, category, paywall,
                http_status, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article_id,
            url,
            domain,
            content.get('title', 'Unknown'),
            content.get('author'),
            now,
            f'rss:{feed_name}',    # use email_account field for source
            f'[RSS] {feed_name}',  # use email_subject for feed name
            'saved',
            fulltext_path,
            abstract,
            content.get('word_count', 0),
            category,
            content.get('paywall', False),
            content.get('http_status', 200),
            content_hash,
        ))
        conn.commit()
        return cursor.rowcount > 0  # True if actually inserted
    finally:
        conn.close()


def main():
    log("=" * 70)
    log("📡 RSS Feed Scanner")
    log("=" * 70)

    config = load_config()
    feeds = config.get('feeds', [])
    state = load_state()
    priority_threshold = config.get('filters', {}).get('priority_threshold', 'low')

    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    threshold_val = priority_order.get(priority_threshold, 3)

    # Sort feeds by priority
    feeds.sort(key=lambda f: priority_order.get(f.get('priority', 'low'), 3))

    log(f"📋 {len(feeds)} feeds configured (threshold: {priority_threshold})")

    stats = {'feeds_scanned': 0, 'articles_found': 0, 'articles_saved': 0,
             'skipped_existing': 0, 'errors': 0, 'feeds_failed': 0}

    for feed in feeds:
        feed_priority = feed.get('priority', 'low')
        if priority_order.get(feed_priority, 3) > threshold_val:
            continue

        feed_name = feed['name']
        feed_url = feed['url']
        category = feed.get('category', 'rss')

        log(f"\n📡 {feed_name} [{feed_priority}]")

        entries, error = parse_feed(feed_url)
        if error:
            log(f"   ❌ {error}")
            stats['feeds_failed'] += 1
            continue

        stats['feeds_scanned'] += 1
        log(f"   Found {len(entries)} entries")

        saved_in_feed = 0
        for entry in entries:
            url = entry['url']
            stats['articles_found'] += 1

            if url_exists(url):
                stats['skipped_existing'] += 1
                continue

            # Fetch full article
            content = fetch_article(url)
            if 'error' in content:
                log(f"   ❌ {entry['title'][:40]}... - {content['error']}")
                stats['errors'] += 1
                time.sleep(REQUEST_DELAY)
                continue

            # Use feed entry title if page title is generic
            if content.get('title') in ('Unknown', '', None) and entry.get('title'):
                content['title'] = entry['title']

            # Use RSS description as fallback abstract
            if entry.get('description') and not content.get('text'):
                # Strip HTML from description
                desc_soup = BeautifulSoup(entry['description'], 'html.parser')
                content['text'] = desc_soup.get_text(strip=True)
                content['word_count'] = len(content['text'].split())

            inserted = insert_article(url, content, feed_name, category, feed_priority)
            if inserted:
                saved_in_feed += 1
                stats['articles_saved'] += 1
                log(f"   ✅ {content['title'][:60]}...")

            time.sleep(REQUEST_DELAY)

        if saved_in_feed:
            log(f"   📊 Saved {saved_in_feed} new articles from {feed_name}")

        # Update state
        state[feed_name] = {
            'last_scan': datetime.now().isoformat(),
            'entries_found': len(entries),
            'articles_saved': saved_in_feed,
        }
        save_state(state)

    log("\n" + "=" * 70)
    log("📊 RSS SCAN SUMMARY")
    log("=" * 70)
    log(f"Feeds scanned:     {stats['feeds_scanned']}")
    log(f"Feeds failed:      {stats['feeds_failed']}")
    log(f"Articles found:    {stats['articles_found']}")
    log(f"Articles saved:    {stats['articles_saved']}")
    log(f"Already existing:  {stats['skipped_existing']}")
    log(f"Errors:            {stats['errors']}")
    log(f"\n✅ Done! Log saved to: {LOG_FILE}")


if __name__ == '__main__':
    main()
