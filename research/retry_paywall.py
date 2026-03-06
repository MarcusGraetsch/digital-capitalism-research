#!/usr/bin/env python3
"""
Paywall Retry - Re-attempt fetching paywall-blocked articles.
Tries different strategies: alternate headers, Google cache, archive.org.
"""

import os
import re
import json
import sqlite3
import hashlib
import time
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, quote
from bs4 import BeautifulSoup

RESEARCH_DIR = Path(os.environ.get('RESEARCH_DIR', '/root/.openclaw/workspace/research'))
DB_FILE = RESEARCH_DIR / 'articles.db'
FULLTEXT_DIR = RESEARCH_DIR / 'fulltext'
LOG_FILE = RESEARCH_DIR / 'retry_paywall.log'
MAX_RETRIES_PER_RUN = 50
REQUEST_DELAY = 2.0


def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def get_paywall_articles(limit=MAX_RETRIES_PER_RUN):
    """Get articles marked as paywall_preview"""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, url, domain, title, category, fulltext_path,
                   paywall_type, error_message
            FROM articles
            WHERE content_status = 'paywall_preview'
            ORDER BY access_date DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# --- Fetch strategies ---

USER_AGENTS = [
    # Googlebot (some sites serve full content to crawlers)
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    # Standard browser with different locale
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # Curl-like (some sites don't paywall simple clients)
    'curl/8.0',
]


def fetch_with_headers(url, user_agent):
    """Fetch with a specific user agent"""
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'DNT': '1',
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
    except requests.RequestException:
        pass
    return None


def fetch_from_archive(url):
    """Try to get the article from archive.org's Wayback Machine"""
    try:
        # Check if archived
        api_url = f"https://archive.org/wayback/available?url={quote(url)}"
        resp = requests.get(api_url, timeout=15)
        if resp.status_code != 200:
            return None

        data = resp.json()
        snapshot = data.get('archived_snapshots', {}).get('closest', {})
        if not snapshot.get('available'):
            return None

        archive_url = snapshot['url']
        resp = requests.get(archive_url, timeout=30,
                            headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            return resp.text
    except (requests.RequestException, ValueError):
        pass
    return None


def fetch_from_google_cache(url):
    """Try Google's cached version"""
    try:
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{quote(url)}"
        resp = requests.get(cache_url, timeout=30,
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        if resp.status_code == 200 and len(resp.text) > 1000:
            return resp.text
    except requests.RequestException:
        pass
    return None


def extract_content(html):
    """Extract article text from HTML"""
    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()

    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else 'Unknown'

    article = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile('content|article'))
    if article:
        text = article.get_text(separator='\n', strip=True)
    else:
        text = soup.get_text(separator='\n', strip=True)

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n\n'.join(lines)

    return title, text


def is_real_content(text):
    """Check if fetched content is substantial (not just another paywall page)"""
    word_count = len(text.split())
    if word_count < 200:
        return False

    paywall_words = [
        'abonnieren', 'subscribe', 'paywall', 'premium',
        'login to read', 'registrieren', 'bitte anmelden'
    ]
    paywall_count = sum(1 for w in paywall_words if w in text.lower())
    if paywall_count >= 3 and word_count < 500:
        return False

    return True


def save_fulltext(url, title, text, category):
    """Save the successfully fetched article"""
    now = datetime.now()
    dir_path = FULLTEXT_DIR / now.strftime('%Y-%m')
    dir_path.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    domain = urlparse(url).netloc.replace('www.', '')
    filename = f"{url_hash}_{domain}.md"
    file_path = dir_path / filename

    word_count = len(text.split())
    header = f"""---
url: {url}
title: {title}
domain: {domain}
category: {category}
date_scanned: {now.isoformat()}
word_count: {word_count}
paywall: false
retry_success: true
---

# {title}

**URL:** {url}

**Domain:** {domain}

**Category:** {category}

**Scanned:** {now.isoformat()}

**Word Count:** {word_count}

---

{text}
"""

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(header)

    return str(file_path), word_count


def update_article_success(article_id, fulltext_path, word_count, abstract):
    """Update article to 'saved' status after successful retry"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articles
            SET content_status = 'saved',
                fulltext_path = ?,
                word_count = ?,
                abstract = ?,
                paywall = 0,
                error_message = NULL
            WHERE id = ?
        ''', (fulltext_path, word_count, abstract, article_id))
        conn.commit()
    finally:
        conn.close()


def update_retry_failed(article_id):
    """Mark that retry was attempted but failed"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articles
            SET error_message = COALESCE(error_message, '') || ' | retry_failed:' || ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), article_id))
        conn.commit()
    finally:
        conn.close()


def retry_article(article):
    """Try all strategies to fetch a paywall article"""
    url = article['url']

    # Strategy 1: Different user agents
    for ua in USER_AGENTS:
        html = fetch_with_headers(url, ua)
        if html:
            title, text = extract_content(html)
            if is_real_content(text):
                return title, text, 'alt_headers'
        time.sleep(1)

    # Strategy 2: Google cache
    html = fetch_from_google_cache(url)
    if html:
        title, text = extract_content(html)
        if is_real_content(text):
            return title, text, 'google_cache'

    time.sleep(1)

    # Strategy 3: Archive.org
    html = fetch_from_archive(url)
    if html:
        title, text = extract_content(html)
        if is_real_content(text):
            return title, text, 'archive_org'

    return None, None, None


def main():
    log("=" * 70)
    log("🔓 Paywall Retry - Re-attempting blocked articles")
    log("=" * 70)

    articles = get_paywall_articles()
    log(f"\n📊 {len(articles)} paywall articles to retry\n")

    if not articles:
        log("✅ No paywall articles to retry!")
        return

    stats = {'success': 0, 'failed': 0}

    for idx, article in enumerate(articles, 1):
        log(f"\n[{idx}/{len(articles)}] {article['title'][:60]}...")
        log(f"   URL: {article['url'][:80]}")

        title, text, strategy = retry_article(article)

        if text:
            fulltext_path, word_count = save_fulltext(
                article['url'], title, text, article['category']
            )
            abstract = text[:500] + '...' if len(text) > 500 else text
            update_article_success(article['id'], fulltext_path, word_count, abstract)
            log(f"   ✅ Success via {strategy} ({word_count} words)")
            stats['success'] += 1
        else:
            update_retry_failed(article['id'])
            log(f"   ❌ All strategies failed")
            stats['failed'] += 1

        time.sleep(REQUEST_DELAY)

    log("\n" + "=" * 70)
    log("📊 RETRY SUMMARY")
    log("=" * 70)
    log(f"Recovered:  {stats['success']}")
    log(f"Still blocked: {stats['failed']}")
    log(f"\n✅ Done! Log saved to: {LOG_FILE}")


if __name__ == '__main__':
    main()
