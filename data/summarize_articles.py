#!/usr/bin/env python3
"""
Article Summarizer - LLM-based summarization
Uses the summarize CLI to generate real summaries for labeled articles.
Runs after label_articles.py in the pipeline.
"""

import os
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
import time

RESEARCH_DIR = Path(os.environ.get('RESEARCH_DIR', '/root/.openclaw/workspace/research'))
DB_FILE = RESEARCH_DIR / 'articles.db'
LOG_FILE = RESEARCH_DIR / 'summarize.log'
BATCH_SIZE = 10
# Only summarize articles above this word count (skip tiny ones)
MIN_WORDS_FOR_SUMMARY = 200
# Delay between summarize calls to respect rate limits
REQUEST_DELAY = 2.0

def log(msg):
    """Log to file and print"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def get_articles_to_summarize(limit=BATCH_SIZE):
    """Get labeled articles that need real summaries"""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Target labeled articles that still have placeholder summaries
        # (abstract starts with 'Artikel über' or is just the first 500 chars)
        cursor.execute('''
            SELECT id, url, domain, title, fulltext_path, abstract,
                   word_count, tags, category
            FROM articles
            WHERE content_status = 'labeled'
            AND word_count >= ?
            AND (summary IS NULL OR summary = '')
            ORDER BY
                CASE WHEN tags LIKE '%high%' THEN 0
                     WHEN tags LIKE '%medium%' THEN 1
                     ELSE 2 END,
                word_count DESC
            LIMIT ?
        ''', (MIN_WORDS_FOR_SUMMARY, limit))

        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def count_remaining():
    """Count articles still needing summaries"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM articles
            WHERE content_status = 'labeled'
            AND word_count >= ?
            AND (summary IS NULL OR summary = '')
        ''', (MIN_WORDS_FOR_SUMMARY,))
        return cursor.fetchone()[0]
    finally:
        conn.close()

def ensure_summary_column():
    """Add summary column to articles table if it doesn't exist"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'summary' not in columns:
            cursor.execute('ALTER TABLE articles ADD COLUMN summary TEXT')
            conn.commit()
            log("Added 'summary' column to articles table")
    finally:
        conn.close()

def summarize_with_cli(url):
    """Use the summarize CLI to get an article summary"""
    try:
        result = subprocess.run(
            [
                'summarize', url,
                '--length', 'short',
                '--json'
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return None, f"summarize CLI failed: {result.stderr[:200]}"

        try:
            data = json.loads(result.stdout)
            summary = data.get('summary', '') or data.get('text', '') or result.stdout.strip()
            return summary, None
        except json.JSONDecodeError:
            # CLI returned plain text instead of JSON
            summary = result.stdout.strip()
            if summary and len(summary) > 20:
                return summary, None
            return None, f"Invalid output: {result.stdout[:200]}"

    except subprocess.TimeoutExpired:
        return None, "Timeout after 60s"
    except FileNotFoundError:
        return None, "summarize CLI not installed"
    except Exception as e:
        return None, str(e)

def summarize_from_fulltext(fulltext_path):
    """Fallback: generate a basic extractive summary from the fulltext file"""
    file_path = Path(fulltext_path)
    if not file_path.is_absolute():
        file_path = RESEARCH_DIR / fulltext_path

    if not file_path.exists():
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip frontmatter
    lines = content.split('\n')
    in_content = False
    content_lines = []
    for line in lines:
        if line.strip() == '---' and not in_content:
            in_content = True
            continue
        if in_content:
            stripped = line.strip()
            if stripped and not stripped.startswith('**') and not stripped.startswith('#'):
                content_lines.append(stripped)

    # Take first 3 substantial sentences as extractive summary
    text = ' '.join(content_lines)
    sentences = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 30]
    if sentences:
        return ' '.join(sentences[:3])
    return None

def update_article_summary(article_id, summary):
    """Store the summary in the database"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE articles
            SET summary = ?
            WHERE id = ?
        ''', (summary, article_id))
        conn.commit()
    finally:
        conn.close()

def main():
    log("=" * 70)
    log("📝 Article Summarizer - LLM-based summaries")
    log("=" * 70)

    ensure_summary_column()

    total_remaining = count_remaining()
    log(f"\n📊 {total_remaining} articles need summaries\n")

    if total_remaining == 0:
        log("✅ All articles already summarized!")
        return

    stats = {'summarized': 0, 'fallback': 0, 'errors': 0}
    batch_num = 0

    while True:
        articles = get_articles_to_summarize(BATCH_SIZE)

        if not articles:
            break

        batch_num += 1
        log(f"\n📦 Batch {batch_num}: Summarizing {len(articles)} articles...")

        for article in articles:
            try:
                # Try summarize CLI first (uses the article URL)
                summary, error = summarize_with_cli(article['url'])

                if summary:
                    update_article_summary(article['id'], summary)
                    log(f"   📝 {article['title'][:50]}... [CLI]")
                    stats['summarized'] += 1
                else:
                    # Fallback to extractive summary from fulltext
                    log(f"   ⚠️  CLI failed ({error}), trying fallback...")
                    summary = summarize_from_fulltext(article['fulltext_path'])
                    if summary:
                        update_article_summary(article['id'], summary)
                        log(f"   📝 {article['title'][:50]}... [extractive]")
                        stats['fallback'] += 1
                    else:
                        log(f"   ❌ No summary possible: {article['title'][:50]}...")
                        stats['errors'] += 1

                time.sleep(REQUEST_DELAY)

            except Exception as e:
                log(f"   ❌ Error: {article['title'][:50]}... - {e}")
                stats['errors'] += 1

        remaining = count_remaining()
        log(f"\n📊 Progress: {stats['summarized'] + stats['fallback']} done, {remaining} remaining")

    log("\n" + "=" * 70)
    log("📊 FINAL SUMMARY")
    log("=" * 70)
    log(f"Summarized (CLI):        {stats['summarized']}")
    log(f"Summarized (extractive): {stats['fallback']}")
    log(f"Errors:                  {stats['errors']}")
    log(f"\n✅ Done! Log saved to: {LOG_FILE}")

if __name__ == '__main__':
    main()
