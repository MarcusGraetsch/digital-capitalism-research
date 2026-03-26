#!/usr/bin/env python3
"""Quotes & Excerpts CLI — browse, search, curate, and export.

Usage:
    python -m literature_pipeline.quotes list                    # List recent quotes
    python -m literature_pipeline.quotes list --type quote       # Only verbatim quotes
    python -m literature_pipeline.quotes list --type excerpt     # Only excerpts
    python -m literature_pipeline.quotes list --quote-type polemic
    python -m literature_pipeline.quotes list --author Marx
    python -m literature_pipeline.quotes list --min-rating 3
    python -m literature_pipeline.quotes list --status curated

    python -m literature_pipeline.quotes search "surveillance"   # Full-text search
    python -m literature_pipeline.quotes stats                   # Show statistics

    python -m literature_pipeline.quotes rate ID RATING          # Rate 0-5
    python -m literature_pipeline.quotes curate ID               # Mark as curated
    python -m literature_pipeline.quotes tag ID "topic1,topic2"  # Add topics
    python -m literature_pipeline.quotes set-type ID polemic     # Change quote_type
    python -m literature_pipeline.quotes set-use ID "website,epigraph"

    python -m literature_pipeline.quotes export-epigraphs        # Export for website
    python -m literature_pipeline.quotes export-json              # Full JSON export
    python -m literature_pipeline.quotes export-markdown          # Markdown collection
"""

import argparse
import json
import sys
import textwrap
from datetime import datetime
from pathlib import Path

from .db import get_connection, init_db, get_quotes, update_quote
from .utils import PIPELINE_DIR


def _wrap(text, width=80, indent="  "):
    """Wrap text with indent."""
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def _display_quote(q, verbose=False):
    """Pretty-print a single quote."""
    q = dict(q)
    entry_type = q.get('entry_type', '?')
    type_icon = '💬' if entry_type == 'quote' else '📝'
    rating = '★' * (q.get('rating', 0) or 0) + '☆' * (5 - (q.get('rating', 0) or 0))
    status = q.get('status', 'new')

    print(f"\n{type_icon} [{q['id']}] {rating}  [{status}]  [{q.get('quote_type', '')}]")
    print(f"  \"{q['text'][:200]}{'...' if len(q.get('text', '')) > 200 else ''}\"")
    print(f"  — {q.get('author', 'Unknown')}, {q.get('source_title', '')}" +
          (f" ({q.get('source_year', '')})" if q.get('source_year') else ""))

    if verbose:
        if q.get('page'):
            print(f"  Page: {q['page']}")
        if q.get('context'):
            print(f"  Context: {q['context'][:100]}")
        if q.get('topics'):
            topics = q['topics']
            if isinstance(topics, str):
                try:
                    topics = json.loads(topics)
                except (json.JSONDecodeError, TypeError):
                    topics = [topics]
            print(f"  Topics: {', '.join(topics) if isinstance(topics, list) else topics}")
        if q.get('found_via'):
            print(f"  Found via: {q['found_via']}")


def cmd_list(args):
    """List quotes with optional filters."""
    conn = init_db()
    quotes = get_quotes(
        conn,
        entry_type=args.type,
        quote_type=args.quote_type,
        status=args.status,
        min_rating=args.min_rating,
        author=args.author,
        limit=args.limit or 20,
    )
    conn.close()

    if not quotes:
        print("No quotes found matching criteria.")
        return

    print(f"\n{'='*70}")
    print(f"Found {len(quotes)} quotes/excerpts")
    print(f"{'='*70}")

    for q in quotes:
        _display_quote(q, verbose=args.verbose)

    print()


def cmd_search(args):
    """Full-text search across quotes."""
    conn = init_db()
    query = args.query
    like = f"%{query}%"
    results = conn.execute(
        """SELECT * FROM quotes
           WHERE text LIKE ? OR author LIKE ? OR source_title LIKE ?
              OR context LIKE ? OR topics LIKE ?
           ORDER BY rating DESC, created_at DESC
           LIMIT ?""",
        (like, like, like, like, like, args.limit or 20),
    ).fetchall()
    conn.close()

    if not results:
        print(f"No quotes matching '{query}'")
        return

    print(f"\n{'='*70}")
    print(f"Search results for '{query}': {len(results)} matches")
    print(f"{'='*70}")

    for q in results:
        _display_quote(q, verbose=True)

    print()


def cmd_stats(args):
    """Show quote database statistics."""
    conn = init_db()

    total = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    print(f"\nTotal entries: {total}")

    print("\nBy entry type:")
    for row in conn.execute("SELECT entry_type, COUNT(*) FROM quotes GROUP BY entry_type"):
        print(f"  {row[0]}: {row[1]}")

    print("\nBy quote type:")
    for row in conn.execute("SELECT quote_type, COUNT(*) FROM quotes GROUP BY quote_type ORDER BY COUNT(*) DESC"):
        print(f"  {row[0] or 'unclassified'}: {row[1]}")

    print("\nBy source:")
    for row in conn.execute("SELECT found_via, COUNT(*) FROM quotes GROUP BY found_via ORDER BY COUNT(*) DESC"):
        print(f"  {row[0] or 'unknown'}: {row[1]}")

    print("\nBy status:")
    for row in conn.execute("SELECT status, COUNT(*) FROM quotes GROUP BY status"):
        print(f"  {row[0]}: {row[1]}")

    print("\nBy rating:")
    for row in conn.execute("SELECT rating, COUNT(*) FROM quotes GROUP BY rating ORDER BY rating DESC"):
        r = row[0] or 0
        print(f"  {'★' * r + '☆' * (5 - r)}: {row[1]}")

    print("\nTop 10 quoted authors:")
    for row in conn.execute("SELECT author, COUNT(*) FROM quotes GROUP BY author ORDER BY COUNT(*) DESC LIMIT 10"):
        print(f"  {row[0]}: {row[1]}")

    conn.close()
    print()


def cmd_rate(args):
    """Rate a quote."""
    conn = init_db()
    update_quote(conn, args.id, rating=args.rating)
    conn.close()
    print(f"Quote {args.id} rated {'★' * args.rating}{'☆' * (5 - args.rating)}")


def cmd_curate(args):
    """Mark a quote as curated."""
    conn = init_db()
    update_quote(conn, args.id, status='curated')
    conn.close()
    print(f"Quote {args.id} marked as curated")


def cmd_tag(args):
    """Add topics to a quote."""
    conn = init_db()
    topics = [t.strip() for t in args.topics.split(',')]
    update_quote(conn, args.id, topics=topics)
    conn.close()
    print(f"Quote {args.id} tagged: {', '.join(topics)}")


def cmd_set_type(args):
    """Change quote_type."""
    conn = init_db()
    update_quote(conn, args.id, quote_type=args.quote_type)
    conn.close()
    print(f"Quote {args.id} type set to: {args.quote_type}")


def cmd_set_use(args):
    """Set use_for field."""
    conn = init_db()
    uses = [u.strip() for u in args.uses.split(',')]
    update_quote(conn, args.id, use_for=uses)
    conn.close()
    print(f"Quote {args.id} use_for set to: {', '.join(uses)}")


def cmd_export_epigraphs(args):
    """Export curated quotes as epigraphs.json for the website."""
    conn = init_db()

    # Get quotes marked for website/epigraph use, or highly rated curated quotes
    results = conn.execute("""
        SELECT * FROM quotes
        WHERE (use_for LIKE '%epigraph%' OR use_for LIKE '%website%')
           OR (status = 'curated' AND rating >= 4 AND entry_type = 'quote')
        ORDER BY rating DESC, created_at DESC
    """).fetchall()
    conn.close()

    if not results:
        print("No quotes ready for epigraph export. Curate and rate some first.")
        return

    epigraphs = []
    for i, q in enumerate(results, 1):
        q = dict(q)
        year = f", {q['source_year']}" if q.get('source_year') else ""
        epigraphs.append({
            "id": f"{i:03d}",
            "quote": q['text'],
            "author": q.get('author', 'Unknown'),
            "source": f"{q.get('source_title', '')}{year}",
            "date": datetime.now().strftime('%Y-%m'),
            "current": i == 1,
        })

    output_path = args.output or str(
        Path(__file__).resolve().parent.parent / "exports" / "epigraphs.json"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(epigraphs, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(epigraphs)} epigraphs to {output_path}")


def cmd_export_json(args):
    """Full JSON export of all quotes."""
    conn = init_db()
    results = conn.execute("SELECT * FROM quotes ORDER BY rating DESC, created_at DESC").fetchall()
    conn.close()

    quotes = []
    for q in results:
        q = dict(q)
        for field in ('topics', 'use_for'):
            if q.get(field) and isinstance(q[field], str):
                try:
                    q[field] = json.loads(q[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        quotes.append(q)

    output_path = args.output or str(
        Path(__file__).resolve().parent.parent / "exports" / "quotes.json"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(quotes)} quotes to {output_path}")


def cmd_export_markdown(args):
    """Export quotes as a readable markdown collection."""
    conn = init_db()
    results = conn.execute("""
        SELECT * FROM quotes
        WHERE rating >= ?
        ORDER BY author, source_year, created_at
    """, (args.min_rating or 0,)).fetchall()
    conn.close()

    if not results:
        print("No quotes to export.")
        return

    lines = [
        f"# Quotes & Excerpts Collection",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total entries: {len(results)}",
        "",
    ]

    # Group by author
    by_author = {}
    for q in results:
        q = dict(q)
        author = q.get('author', 'Unknown')
        by_author.setdefault(author, []).append(q)

    for author in sorted(by_author.keys()):
        lines.append(f"\n## {author}\n")
        for q in by_author[author]:
            rating = '★' * (q.get('rating', 0) or 0)
            entry_type = q.get('entry_type', '?')
            icon = '💬' if entry_type == 'quote' else '📝'

            if entry_type == 'quote':
                lines.append(f"{icon} > \"{q['text']}\"")
            else:
                lines.append(f"{icon} {q['text']}")

            source_info = q.get('source_title', '')
            if q.get('source_year'):
                source_info += f" ({q['source_year']})"
            if q.get('page'):
                source_info += f", p. {q['page']}"

            lines.append(f"  *{source_info}* {rating}")
            lines.append(f"  [{q.get('quote_type', '')}] [{q.get('found_via', '')}]")
            lines.append("")

    output_path = args.output or str(
        Path(__file__).resolve().parent.parent / "exports" / "quotes.md"
    )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Exported {len(results)} quotes to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Quotes & Excerpts CLI')
    sub = parser.add_subparsers(dest='command')

    # list
    p_list = sub.add_parser('list', help='List quotes')
    p_list.add_argument('--type', choices=['quote', 'excerpt'])
    p_list.add_argument('--quote-type')
    p_list.add_argument('--author')
    p_list.add_argument('--status')
    p_list.add_argument('--min-rating', type=int)
    p_list.add_argument('--limit', type=int, default=20)
    p_list.add_argument('-v', '--verbose', action='store_true')

    # search
    p_search = sub.add_parser('search', help='Full-text search')
    p_search.add_argument('query')
    p_search.add_argument('--limit', type=int, default=20)

    # stats
    sub.add_parser('stats', help='Show statistics')

    # rate
    p_rate = sub.add_parser('rate', help='Rate a quote (0-5)')
    p_rate.add_argument('id', type=int)
    p_rate.add_argument('rating', type=int, choices=range(6))

    # curate
    p_curate = sub.add_parser('curate', help='Mark as curated')
    p_curate.add_argument('id', type=int)

    # tag
    p_tag = sub.add_parser('tag', help='Add topics')
    p_tag.add_argument('id', type=int)
    p_tag.add_argument('topics', help='Comma-separated topics')

    # set-type
    p_stype = sub.add_parser('set-type', help='Change quote_type')
    p_stype.add_argument('id', type=int)
    p_stype.add_argument('quote_type')

    # set-use
    p_suse = sub.add_parser('set-use', help='Set use_for')
    p_suse.add_argument('id', type=int)
    p_suse.add_argument('uses', help='Comma-separated: website,epigraph,article,social_media')

    # export-epigraphs
    p_epi = sub.add_parser('export-epigraphs', help='Export as epigraphs.json')
    p_epi.add_argument('--output', help='Output path')

    # export-json
    p_json = sub.add_parser('export-json', help='Full JSON export')
    p_json.add_argument('--output', help='Output path')

    # export-markdown
    p_md = sub.add_parser('export-markdown', help='Markdown collection')
    p_md.add_argument('--output', help='Output path')
    p_md.add_argument('--min-rating', type=int, default=0)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        'list': cmd_list,
        'search': cmd_search,
        'stats': cmd_stats,
        'rate': cmd_rate,
        'curate': cmd_curate,
        'tag': cmd_tag,
        'set-type': cmd_set_type,
        'set-use': cmd_set_use,
        'export-epigraphs': cmd_export_epigraphs,
        'export-json': cmd_export_json,
        'export-markdown': cmd_export_markdown,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
