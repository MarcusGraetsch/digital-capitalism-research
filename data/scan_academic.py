#!/usr/bin/env python3
"""
Academic Paper Monitor — OpenAlex-based alerting system.
Checks for new publications by tracked authors and keyword searches,
generates a weekly digest of relevant papers.

Usage:
    python3 research/scan_academic.py                  # Full scan + digest
    python3 research/scan_academic.py --authors-only   # Only check author publications
    python3 research/scan_academic.py --keywords-only  # Only run keyword searches
    python3 research/scan_academic.py --digest-only    # Regenerate digest from DB
    python3 research/scan_academic.py --stats          # Show database stats
"""

import os
import json
import sqlite3
import hashlib
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote

RESEARCH_DIR = Path(os.environ.get('RESEARCH_DIR', '/root/.openclaw/workspace/research'))
REPO_ROOT = RESEARCH_DIR.parent
CONFIG_FILE = RESEARCH_DIR / 'academic_config.json'
DB_FILE = RESEARCH_DIR / 'academic_papers.db'
LOG_FILE = RESEARCH_DIR / 'scan_academic.log'
STATE_FILE = RESEARCH_DIR / 'academic_state.json'

API_BASE = 'https://api.openalex.org'
REQUEST_DELAY = 0.5  # OpenAlex is generous but be polite


def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_FILE}")
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    openalex_id TEXT UNIQUE,
    title TEXT NOT NULL,
    authors TEXT,
    year INTEGER,
    publication_date TEXT,
    doi TEXT,
    journal TEXT,
    abstract TEXT,
    open_access_url TEXT,
    cited_by_count INTEGER DEFAULT 0,
    source_type TEXT,
    topics TEXT,
    found_via TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'new',
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def paper_exists(openalex_id):
    conn = get_connection()
    try:
        row = conn.execute(
            'SELECT id FROM papers WHERE openalex_id = ?', (openalex_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# OpenAlex API
# ---------------------------------------------------------------------------

def openalex_request(endpoint, params=None):
    """Make a request to OpenAlex API with polite pool."""
    config = load_config()
    email = config.get('settings', {}).get('email', '')

    if params is None:
        params = {}
    if email:
        params['mailto'] = email

    url = f"{API_BASE}{endpoint}"

    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"HTTP {resp.status_code}"
    except requests.RequestException as e:
        return None, str(e)


def parse_work(work):
    """Parse an OpenAlex work object into our paper dict."""
    openalex_id = work.get('id', '').replace('https://openalex.org/', '')

    # Authors
    authorships = work.get('authorships', [])
    authors = [a.get('author', {}).get('display_name', '') for a in authorships]
    authors = [a for a in authors if a]

    # Journal/source
    source = work.get('primary_location', {}) or {}
    source_obj = source.get('source', {}) or {}
    journal = source_obj.get('display_name', '')

    # Open access URL
    oa_url = None
    oa = work.get('open_access', {}) or {}
    oa_url = oa.get('oa_url')
    if not oa_url:
        best_loc = work.get('best_oa_location', {}) or {}
        oa_url = best_loc.get('pdf_url') or best_loc.get('landing_page_url')

    # Abstract — OpenAlex uses inverted index format
    abstract = _reconstruct_abstract(work.get('abstract_inverted_index'))

    # Topics
    topics = work.get('topics', []) or []
    topic_names = [t.get('display_name', '') for t in topics[:5]]

    return {
        'openalex_id': openalex_id,
        'title': work.get('title', 'Untitled'),
        'authors': json.dumps(authors),
        'year': work.get('publication_year'),
        'publication_date': work.get('publication_date'),
        'doi': work.get('doi'),
        'journal': journal,
        'abstract': abstract,
        'open_access_url': oa_url,
        'cited_by_count': work.get('cited_by_count', 0),
        'source_type': work.get('type', ''),
        'topics': json.dumps(topic_names),
    }


def _reconstruct_abstract(inverted_index):
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return None

    try:
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort()
        return ' '.join(word for _, word in word_positions)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Author Monitoring
# ---------------------------------------------------------------------------

def scan_author(author_config, lookback_days):
    """Check for new publications by a tracked author."""
    name = author_config['name']
    author_id = author_config['openalex_id']

    from_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

    log(f"   Checking {name} (since {from_date})...")

    data, error = openalex_request('/works', {
        'filter': f'author.id:{author_id},from_publication_date:{from_date}',
        'sort': 'publication_date:desc',
        'per_page': 25,
    })

    if error:
        log(f"   API error: {error}")
        return []

    results = data.get('results', [])
    new_papers = []

    for work in results:
        paper = parse_work(work)
        if paper_exists(paper['openalex_id']):
            continue

        paper['found_via'] = f"author:{name}"
        paper['priority'] = 'high'
        new_papers.append(paper)

    return new_papers


# ---------------------------------------------------------------------------
# Keyword Monitoring
# ---------------------------------------------------------------------------

def scan_keywords(keyword_config, lookback_days):
    """Search for new papers matching a keyword query."""
    query = keyword_config['query']
    priority = keyword_config.get('priority', 'medium')
    max_results = 20

    from_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

    log(f"   Searching: \"{query}\" (since {from_date})...")

    data, error = openalex_request('/works', {
        'search': query,
        'filter': f'from_publication_date:{from_date},type:article|book-chapter|book|review',
        'sort': 'relevance_score:desc',
        'per_page': max_results,
    })

    if error:
        log(f"   API error: {error}")
        return []

    results = data.get('results', [])
    new_papers = []

    for work in results:
        paper = parse_work(work)
        if paper_exists(paper['openalex_id']):
            continue

        paper['found_via'] = f"keyword:{query}"
        paper['priority'] = priority
        new_papers.append(paper)

    return new_papers


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def store_papers(papers):
    """Insert new papers into the database."""
    if not papers:
        return 0

    conn = get_connection()
    inserted = 0
    try:
        for paper in papers:
            paper_id = hashlib.md5(paper['openalex_id'].encode()).hexdigest()
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO papers
                    (id, openalex_id, title, authors, year, publication_date,
                     doi, journal, abstract, open_access_url, cited_by_count,
                     source_type, topics, found_via, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    paper_id,
                    paper['openalex_id'],
                    paper['title'],
                    paper['authors'],
                    paper['year'],
                    paper['publication_date'],
                    paper['doi'],
                    paper['journal'],
                    paper['abstract'],
                    paper['open_access_url'],
                    paper['cited_by_count'],
                    paper['source_type'],
                    paper['topics'],
                    paper['found_via'],
                    paper['priority'],
                ))
                if conn.total_changes:
                    inserted += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
    finally:
        conn.close()

    return inserted


# ---------------------------------------------------------------------------
# Digest Generation
# ---------------------------------------------------------------------------

def generate_digest(lookback_days=30):
    """Generate a markdown digest of recent papers."""
    config = load_config()
    settings = config.get('settings', {})
    digest_dir = Path(REPO_ROOT) / settings.get('digest_dir', 'news')
    digest_dir.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    try:
        cutoff = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        papers = conn.execute('''
            SELECT * FROM papers
            WHERE created_at >= ? OR publication_date >= ?
            ORDER BY
                CASE priority
                    WHEN 'high' THEN 0
                    WHEN 'medium' THEN 1
                    WHEN 'low' THEN 2
                END,
                publication_date DESC
        ''', (cutoff, cutoff)).fetchall()
    finally:
        conn.close()

    if not papers:
        log("   No papers found for digest")
        return None

    now = datetime.now()
    filename = f"{now.strftime('%Y-%m')}-academic-digest.md"
    filepath = digest_dir / filename

    lines = [
        f"# Academic Paper Digest — {now.strftime('%B %Y')}",
        f"\nGenerated: {now.strftime('%Y-%m-%d %H:%M')}",
        f"Papers found: {len(papers)}",
        "",
    ]

    # Group by found_via
    by_source = {}
    for p in papers:
        p = dict(p)
        source = p.get('found_via', 'unknown')
        by_source.setdefault(source, []).append(p)

    # Author papers first
    author_sources = sorted([s for s in by_source if s.startswith('author:')])
    keyword_sources = sorted([s for s in by_source if s.startswith('keyword:')])

    if author_sources:
        lines.append("## Tracked Author Publications\n")
        for source in author_sources:
            author_name = source.replace('author:', '')
            lines.append(f"### {author_name}\n")
            for p in by_source[source]:
                _format_paper(p, lines)
            lines.append("")

    if keyword_sources:
        lines.append("## Keyword Search Results\n")
        for source in keyword_sources:
            keyword = source.replace('keyword:', '')
            lines.append(f"### \"{keyword}\"\n")
            for p in by_source[source]:
                _format_paper(p, lines)
            lines.append("")

    content = '\n'.join(lines)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    log(f"   Digest saved: {filepath}")
    return filepath


def _format_paper(paper, lines):
    """Format a single paper for the digest."""
    authors = json.loads(paper.get('authors', '[]'))
    author_str = ', '.join(authors[:3])
    if len(authors) > 3:
        author_str += ' et al.'

    priority_flag = '🔴' if paper['priority'] == 'high' else '🟡' if paper['priority'] == 'medium' else '⚪'

    lines.append(f"- {priority_flag} **{paper['title']}**")
    lines.append(f"  - {author_str} ({paper.get('year', '?')})")

    if paper.get('journal'):
        lines.append(f"  - *{paper['journal']}*")

    if paper.get('doi'):
        lines.append(f"  - DOI: {paper['doi']}")
    if paper.get('open_access_url'):
        lines.append(f"  - Open Access: {paper['open_access_url']}")

    if paper.get('abstract'):
        abstract = paper['abstract'][:300]
        if len(paper['abstract']) > 300:
            abstract += '...'
        lines.append(f"  - {abstract}")

    lines.append("")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def show_stats():
    """Show database statistics."""
    conn = get_connection()
    try:
        total = conn.execute('SELECT COUNT(*) FROM papers').fetchone()[0]
        log(f"\nTotal papers: {total}")

        rows = conn.execute(
            'SELECT priority, COUNT(*) FROM papers GROUP BY priority ORDER BY priority'
        ).fetchall()
        for priority, count in rows:
            log(f"  {priority}: {count}")

        log("\nBy source:")
        rows = conn.execute(
            'SELECT found_via, COUNT(*) FROM papers GROUP BY found_via ORDER BY COUNT(*) DESC'
        ).fetchall()
        for source, count in rows:
            log(f"  {source}: {count}")

        log("\nBy year:")
        rows = conn.execute(
            'SELECT year, COUNT(*) FROM papers GROUP BY year ORDER BY year DESC LIMIT 5'
        ).fetchall()
        for year, count in rows:
            log(f"  {year}: {count}")

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Academic Paper Monitor (OpenAlex)')
    parser.add_argument('--authors-only', action='store_true', help='Only check tracked authors')
    parser.add_argument('--keywords-only', action='store_true', help='Only run keyword searches')
    parser.add_argument('--digest-only', action='store_true', help='Only regenerate digest')
    parser.add_argument('--stats', action='store_true', help='Show database stats')
    parser.add_argument('--lookback', type=int, help='Override lookback days')
    args = parser.parse_args()

    log("=" * 70)
    log("📚 Academic Paper Monitor (OpenAlex)")
    log("=" * 70)

    config = load_config()
    init_db()

    settings = config.get('settings', {})
    lookback_days = args.lookback or settings.get('lookback_days', 30)

    if args.stats:
        show_stats()
        return

    if args.digest_only:
        generate_digest(lookback_days)
        return

    totals = {'author_papers': 0, 'keyword_papers': 0, 'stored': 0}

    # Scan tracked authors
    if not args.keywords_only:
        log(f"\n👤 Scanning tracked authors (last {lookback_days} days)...")
        authors = config.get('authors', [])
        all_author_papers = []

        for author in authors:
            papers = scan_author(author, lookback_days)
            if papers:
                log(f"   Found {len(papers)} new papers by {author['name']}")
                all_author_papers.extend(papers)
            time.sleep(REQUEST_DELAY)

        totals['author_papers'] = len(all_author_papers)
        stored = store_papers(all_author_papers)
        totals['stored'] += stored

    # Run keyword searches
    if not args.authors_only:
        log(f"\n🔍 Running keyword searches (last {lookback_days} days)...")
        keywords = config.get('keyword_searches', [])
        all_keyword_papers = []

        for kw in keywords:
            papers = scan_keywords(kw, lookback_days)
            if papers:
                log(f"   Found {len(papers)} new papers for \"{kw['query']}\"")
                all_keyword_papers.extend(papers)
            time.sleep(REQUEST_DELAY)

        totals['keyword_papers'] = len(all_keyword_papers)
        stored = store_papers(all_keyword_papers)
        totals['stored'] += stored

    # Generate digest
    log("\n📄 Generating digest...")
    generate_digest(lookback_days)

    # Update state
    state = load_state()
    state['last_run'] = datetime.now().isoformat()
    state['last_stats'] = totals
    save_state(state)

    log("\n" + "=" * 70)
    log("📊 ACADEMIC SCAN SUMMARY")
    log("=" * 70)
    log(f"Author papers found:    {totals['author_papers']}")
    log(f"Keyword papers found:   {totals['keyword_papers']}")
    log(f"New papers stored:      {totals['stored']}")
    log(f"\n✅ Done! Log: {LOG_FILE}")


if __name__ == '__main__':
    main()
