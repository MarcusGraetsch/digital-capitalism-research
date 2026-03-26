#!/usr/bin/env python3
"""
Weekly Digest Generator
Creates a structured markdown digest from labeled articles in the DB.
Output can feed into research chapters or be used as a standalone overview.
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

RESEARCH_DIR = Path(os.environ.get('RESEARCH_DIR', '/root/.openclaw/workspace/research'))
DB_FILE = RESEARCH_DIR / 'articles.db'
DIGEST_DIR = RESEARCH_DIR / 'digests'


def get_articles_since(days=7):
    """Get labeled articles from the last N days"""
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT id, url, domain, title, author, tags, category,
                   word_count, access_date, summary, abstract, paywall
            FROM articles
            WHERE content_status = 'labeled'
            AND access_date >= ?
            ORDER BY
                CASE category
                    WHEN 'bigtech' THEN 1
                    WHEN 'aigen' THEN 2
                    WHEN 'newwork' THEN 3
                    ELSE 4
                END,
                word_count DESC
        ''', (cutoff,))

        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_stats():
    """Get overall DB statistics"""
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()

        stats = {}
        cursor.execute('SELECT COUNT(*) FROM articles')
        stats['total'] = cursor.fetchone()[0]

        cursor.execute('SELECT content_status, COUNT(*) FROM articles GROUP BY content_status')
        stats['by_status'] = dict(cursor.fetchall())

        cursor.execute('SELECT category, COUNT(*) FROM articles WHERE content_status = "labeled" GROUP BY category')
        stats['by_category'] = dict(cursor.fetchall())

        cursor.execute('''
            SELECT COUNT(*) FROM articles
            WHERE content_status = 'labeled'
            AND access_date >= ?
        ''', ((datetime.now() - timedelta(days=7)).isoformat(),))
        stats['new_this_week'] = cursor.fetchone()[0]

        return stats
    finally:
        conn.close()


def group_by_topic(articles):
    """Group articles by their primary topic tag"""
    groups = defaultdict(list)
    for article in articles:
        tags = (article['tags'] or '').split(', ')
        primary = tags[0] if tags else 'Sonstiges'
        groups[primary].append(article)
    return dict(groups)


def format_article(article):
    """Format a single article as markdown"""
    title = article['title'] or 'Untitled'
    url = article['url']
    domain = article['domain']
    tags = article['tags'] or ''
    summary = article['summary'] or article['abstract'] or ''
    word_count = article['word_count'] or 0
    paywall = ' [PAYWALL]' if article['paywall'] else ''

    # Truncate summary
    if summary and len(summary) > 300:
        summary = summary[:297] + '...'

    lines = []
    lines.append(f"- **[{title}]({url})**{paywall}")
    lines.append(f"  *{domain}* | {word_count} Wörter | {tags}")
    if summary:
        lines.append(f"  > {summary}")
    lines.append("")

    return '\n'.join(lines)


def generate_digest(days=7):
    """Generate the weekly digest markdown"""
    now = datetime.now()
    week_start = now - timedelta(days=days)

    articles = get_articles_since(days)
    stats = get_stats()
    topic_groups = group_by_topic(articles)

    # Topic display order
    topic_order = [
        'KI', 'Big Tech', 'Plattformökonomie', 'Arbeitswelt',
        'Überwachung', 'Digitalisierung', 'Sonstiges'
    ]

    lines = []
    lines.append(f"# Wöchentlicher Research-Digest")
    lines.append(f"")
    lines.append(f"**Zeitraum:** {week_start.strftime('%d.%m.%Y')} – {now.strftime('%d.%m.%Y')}")
    lines.append(f"**Generiert:** {now.strftime('%d.%m.%Y %H:%M')}")
    lines.append(f"")

    # Summary stats
    lines.append(f"## Übersicht")
    lines.append(f"")
    lines.append(f"- **Neue Artikel diese Woche:** {len(articles)}")
    lines.append(f"- **Gesamt in Datenbank:** {stats['total']}")
    lines.append(f"")

    # Status breakdown
    lines.append(f"| Status | Anzahl |")
    lines.append(f"|--------|--------|")
    for status, count in sorted(stats['by_status'].items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {status} | {count} |")
    lines.append(f"")

    if not articles:
        lines.append("*Keine neuen Artikel in diesem Zeitraum.*")
        return '\n'.join(lines)

    # Articles grouped by topic
    lines.append(f"## Artikel nach Thema")
    lines.append(f"")

    for topic in topic_order:
        if topic not in topic_groups:
            continue
        group = topic_groups[topic]
        lines.append(f"### {topic} ({len(group)})")
        lines.append(f"")
        for article in group:
            lines.append(format_article(article))

    # Remaining topics not in the order list
    for topic, group in topic_groups.items():
        if topic not in topic_order:
            lines.append(f"### {topic} ({len(group)})")
            lines.append(f"")
            for article in group:
                lines.append(format_article(article))

    # Category breakdown
    lines.append(f"## Nach Quelle")
    lines.append(f"")
    category_names = {'bigtech': 'Big Tech Analysis', 'aigen': 'AI Chatter', 'newwork': 'New Work Culture'}
    for cat, count in stats.get('by_category', {}).items():
        name = category_names.get(cat, cat)
        lines.append(f"- **{name}:** {count} Artikel")
    lines.append(f"")

    lines.append("---")
    lines.append(f"*Generiert von der Research-Pipeline am {now.strftime('%d.%m.%Y %H:%M')}*")

    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate weekly research digest')
    parser.add_argument('--days', type=int, default=7, help='Number of days to include (default: 7)')
    parser.add_argument('--output', type=str, default=None, help='Output file (default: digests/digest-YYYY-MM-DD.md)')
    parser.add_argument('--stdout', action='store_true', help='Print to stdout instead of file')
    args = parser.parse_args()

    digest = generate_digest(args.days)

    if args.stdout:
        print(digest)
    else:
        DIGEST_DIR.mkdir(parents=True, exist_ok=True)
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = DIGEST_DIR / f"digest-{datetime.now().strftime('%Y-%m-%d')}.md"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(digest)
        print(f"Digest written to: {output_path}")


if __name__ == '__main__':
    main()
