#!/usr/bin/env python3
"""
Extract quotes and excerpts from news articles.
Reads fulltext from articles.db, extracts quotable passages via LLM,
stores them in the shared quotes table (literature_pipeline/literature.db).

Runs after summarize_articles.py in the pipeline. Uses a single LLM call
per article, extracting both quotes and excerpts together.

Usage:
    python3 research/extract_article_quotes.py              # Process new labeled articles
    python3 research/extract_article_quotes.py --limit 5     # Limit batch size
    python3 research/extract_article_quotes.py --reprocess   # Re-extract from already processed
"""

import os
import re
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import time

# Add repo root to path for literature_pipeline imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RESEARCH_DIR = Path(os.environ.get('RESEARCH_DIR', '/root/.openclaw/workspace/research'))
DB_FILE = RESEARCH_DIR / 'articles.db'
LOG_FILE = RESEARCH_DIR / 'extract_quotes.log'

BATCH_SIZE = 10
REQUEST_DELAY = 2.0
MIN_WORDS = 300


def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def ensure_quotes_extracted_column():
    """Add quotes_extracted flag to articles table if missing."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'quotes_extracted' not in columns:
            cursor.execute('ALTER TABLE articles ADD COLUMN quotes_extracted INTEGER DEFAULT 0')
            conn.commit()
            log("Added 'quotes_extracted' column to articles table")
    finally:
        conn.close()


def get_articles(limit=BATCH_SIZE, reprocess=False):
    """Get articles that need quote extraction."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        if reprocess:
            condition = "content_status = 'labeled' AND word_count >= ?"
        else:
            condition = "content_status = 'labeled' AND word_count >= ? AND (quotes_extracted IS NULL OR quotes_extracted = 0)"

        return [dict(r) for r in conn.execute(f'''
            SELECT id, url, domain, title, author, fulltext_path, word_count, category, tags
            FROM articles
            WHERE {condition}
            ORDER BY word_count DESC
            LIMIT ?
        ''', (MIN_WORDS, limit)).fetchall()]
    finally:
        conn.close()


def read_fulltext(fulltext_path):
    """Read article fulltext, skipping frontmatter."""
    path = Path(fulltext_path)
    if not path.is_absolute():
        path = RESEARCH_DIR / fulltext_path

    if not path.exists():
        return None

    text = path.read_text(encoding='utf-8')
    # Skip YAML frontmatter
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            text = parts[2]

    return text.strip()


def extract_quotes_llm(title, author, text):
    """Extract quotes and excerpts from article text using Claude."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None, "ANTHROPIC_API_KEY not set"

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Truncate to fit context
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars]

        prompt = f"""Extract notable quotes and key ideas from this news article for a research database on digital capitalism, platform labor, and political economy.

Title: {title}
Author: {author or 'Unknown'}

Extract:
1. "quotes": 2-6 verbatim quotes — the most quotable, sharp, or insightful passages.
   Each with: text (exact), speaker (author or quoted person), quote_type
   (core_concept, polemic, critique, definition, aphorism, empirical, frequently_cited)
2. "excerpts": 1-4 paraphrased key ideas or arguments (in your own words).
   Each with: content (the distilled idea), concept (what concept it relates to)
3. "mentioned_persons": Array of scholars, thinkers, executives, or other named individuals discussed in the article.
   Each with: name (full name), mention_type (discussion/critique/agreement/name_drop), significance (major/moderate/minor)
4. "mentioned_works": Array of books, reports, or studies explicitly referenced.
   Each with: title, authors (array), year (if mentioned), mention_type (citation/discussion/data_source), significance (major/moderate/minor)

Only extract if genuinely notable. It's fine to return empty arrays for short or uninsightful articles.

Return JSON:
{{
  "quotes": [{{"text": "...", "speaker": "...", "quote_type": "..."}}],
  "excerpts": [{{"content": "...", "concept": "..."}}],
  "mentioned_persons": [{{"name": "...", "mention_type": "...", "significance": "..."}}],
  "mentioned_works": [{{"title": "...", "authors": [...], "year": null, "mention_type": "...", "significance": "..."}}]
}}

Article:
{text}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text
        response_text = re.sub(r'^```json\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        data = json.loads(response_text)
        return data, None

    except Exception as e:
        return None, str(e)


def store_mentions(article, data):
    """Store extracted person/work mentions in literature_pipeline's discourse tables."""
    try:
        from literature_pipeline.db import (
            get_connection as get_lit_conn, init_db as init_lit_db,
            get_or_create_person, get_or_create_work, insert_mention,
        )

        init_lit_db()
        conn = get_lit_conn()
        stored = 0

        for item in data.get('mentioned_persons', []):
            name = item.get('name', '').strip()
            if not name:
                continue
            try:
                person_id = get_or_create_person(conn, name)
                insert_mention(
                    conn,
                    article_id=article.get('id', ''),
                    mentioned_person_id=person_id,
                    mention_type=item.get('mention_type', 'discussion'),
                    significance=item.get('significance', 'minor'),
                    extraction_method='llm',
                    confidence=0.6,
                )
                stored += 1
            except Exception:
                pass

        for item in data.get('mentioned_works', []):
            title = item.get('title', '').strip()
            if not title:
                continue
            try:
                work_id = get_or_create_work(
                    conn, title,
                    authors=item.get('authors'),
                    year=item.get('year'),
                )
                insert_mention(
                    conn,
                    article_id=article.get('id', ''),
                    mentioned_work_id=work_id,
                    mention_type=item.get('mention_type', 'citation'),
                    significance=item.get('significance', 'minor'),
                    extraction_method='llm',
                    confidence=0.6,
                )
                stored += 1
            except Exception:
                pass

        conn.close()
        return stored

    except ImportError:
        return 0


def store_quotes(article, data):
    """Store extracted quotes in literature_pipeline's quotes table."""
    try:
        from literature_pipeline.db import (
            get_connection as get_lit_conn, init_db as init_lit_db,
            insert_quote, quote_exists,
        )

        init_lit_db()
        conn = get_lit_conn()
        stored = 0

        tags = []
        if article.get('tags'):
            try:
                tags = json.loads(article['tags']) if isinstance(article['tags'], str) else article['tags']
            except (json.JSONDecodeError, TypeError):
                tags = [article['tags']]

        for q in data.get('quotes', []):
            text = q.get('text', '').strip()
            if not text:
                continue
            speaker = q.get('speaker', article.get('author', 'Unknown'))
            if not quote_exists(conn, text, speaker):
                insert_quote(
                    conn,
                    text=text,
                    author=speaker,
                    source_title=article.get('title', ''),
                    language='en',
                    entry_type='quote',
                    quote_type=q.get('quote_type', 'core_concept'),
                    topics=tags,
                    context=article.get('title', ''),
                    found_via='news_article',
                    article_id=article.get('id', ''),
                )
                stored += 1

        for ex in data.get('excerpts', []):
            content = ex.get('content', '').strip()
            if not content:
                continue
            if not quote_exists(conn, content):
                insert_quote(
                    conn,
                    text=content,
                    author=article.get('author', article.get('domain', '')),
                    source_title=article.get('title', ''),
                    language='en',
                    entry_type='excerpt',
                    quote_type='core_concept',
                    topics=tags,
                    context=ex.get('concept', ''),
                    found_via='news_article',
                    article_id=article.get('id', ''),
                )
                stored += 1

        conn.close()
        return stored

    except ImportError:
        log("   literature_pipeline not available")
        return 0


def mark_extracted(article_id):
    """Mark article as having quotes extracted."""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute(
            'UPDATE articles SET quotes_extracted = 1 WHERE id = ?',
            (article_id,)
        )
        conn.commit()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Extract quotes from news articles')
    parser.add_argument('--limit', type=int, default=BATCH_SIZE)
    parser.add_argument('--reprocess', action='store_true')
    args = parser.parse_args()

    log("=" * 70)
    log("💬 Article Quote Extractor")
    log("=" * 70)

    ensure_quotes_extracted_column()

    articles = get_articles(limit=args.limit, reprocess=args.reprocess)
    log(f"📋 {len(articles)} articles to process\n")

    if not articles:
        log("✅ No articles need quote extraction")
        return

    stats = {'processed': 0, 'quotes_stored': 0, 'errors': 0}

    for article in articles:
        title = article['title'][:50]
        log(f"📰 {title}...")

        text = read_fulltext(article.get('fulltext_path', ''))
        if not text:
            log(f"   No fulltext available")
            mark_extracted(article['id'])
            continue

        data, error = extract_quotes_llm(
            article.get('title', ''),
            article.get('author', ''),
            text,
        )

        if error:
            log(f"   Error: {error}")
            stats['errors'] += 1
        elif data:
            n_quotes = len(data.get('quotes', []))
            n_excerpts = len(data.get('excerpts', []))
            stored = store_quotes(article, data)
            mention_stored = store_mentions(article, data)
            stats['quotes_stored'] += stored
            stats['processed'] += 1
            n_persons = len(data.get('mentioned_persons', []))
            n_works = len(data.get('mentioned_works', []))
            log(f"   Found {n_quotes} quotes, {n_excerpts} excerpts, stored {stored}")
            if mention_stored:
                log(f"   Mentions: {n_persons} persons, {n_works} works, stored {mention_stored}")

        mark_extracted(article['id'])
        time.sleep(REQUEST_DELAY)

    log("\n" + "=" * 70)
    log("📊 QUOTE EXTRACTION SUMMARY")
    log("=" * 70)
    log(f"Articles processed:  {stats['processed']}")
    log(f"Quotes/excerpts stored: {stats['quotes_stored']}")
    log(f"Errors:              {stats['errors']}")
    log(f"\n✅ Done! Log: {LOG_FILE}")


if __name__ == '__main__':
    main()
