#!/usr/bin/env python3
"""Backfill missing fulltext for articles in articles.db.

The RSS/email ingest only stores metadata. This script fills the gap by
fetching each article that has no ``fulltext_path`` and writing the
extracted Markdown next to the other fulltexts.

Usage::

    # dry-run: report what would be fetched, change nothing (default)
    python3 data/backfill_fulltext.py --limit 50

    # apply: fetch, write files, update the database
    python3 data/backfill_fulltext.py --apply --limit 50

    # only these domains
    python3 data/backfill_fulltext.py --apply --domain labournet.de --domain netzpolitik.org

Exit codes: 0 = ok, 1 = error, 2 = completed with failures.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from researchclaw.web.batch_scraper import BatchScraper, ExtractResult  # noqa: E402

RESEARCH_DIR = Path(os.environ.get("RESEARCH_DIR", "/root/.openclaw/workspace/research"))
FULLTEXT_DIR = RESEARCH_DIR / "fulltext"
DB_FILE = Path(os.environ.get("ARTICLES_DB", REPO_ROOT / "data" / "articles.db"))

# Statuses, die auf einen Endzustand hindeuten — erneut zu versuchen ist
# sinnlos (Paywall, robots-gesperrt, HTTP 410).
TERMINAL_STATUSES = ("paywall", "blocked", "http_410")


def generate_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def content_hash(text: str) -> str | None:
    """Hash of the first 500 words — same normalization as scan_v5/scan_rss."""
    words = text.split()[:500]
    if not words:
        return None
    return hashlib.md5(" ".join(w.lower() for w in words).encode()).hexdigest()


def fulltext_path_for(url: str, when: datetime) -> Path:
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    domain = urlparse(url).netloc.replace("www.", "")
    return FULLTEXT_DIR / when.strftime("%Y-%m") / f"{url_hash}_{domain}.md"


def render_fulltext(result: ExtractResult, category: str, when: datetime) -> str:
    """Render the Markdown file in the same format the ingest writes."""
    domain = urlparse(result.url).netloc.replace("www.", "")
    title = result.title or result.url
    return f"""---
url: {result.url}
title: {title}
domain: {domain}
category: {category}
source: batch-backfill
date_scanned: {when.isoformat()}
word_count: {result.word_count}
paywall: False
---

# {title}

**URL:** {result.url}

**Domain:** {domain}

**Category:** {category}

**Source:** Batch Backfill

**Scanned:** {when.isoformat()}

**Word Count:** {result.word_count}

---

{result.markdown}
"""


def fetch_candidates(
    conn: sqlite3.Connection,
    limit: int | None,
    domains: list[str],
    include_missing_words: bool,
    include_terminal: bool = False,
) -> list[dict]:
    """Select articles that still need a fulltext."""
    where = ["(fulltext_path IS NULL OR fulltext_path = '')"]
    params: list = []

    if include_missing_words:
        where.append("(word_count IS NULL OR word_count = 0)")
    if domains:
        placeholders = ",".join("?" for _ in domains)
        where.append(f"domain IN ({placeholders})")
        params.extend(domains)
    if not include_terminal:
        placeholders = ",".join("?" for _ in TERMINAL_STATUSES)
        where.append(
            f"(content_status IS NULL OR content_status NOT IN ({placeholders}))"
        )
        params.extend(TERMINAL_STATUSES)

    sql = (
        "SELECT id, url, domain, title, category FROM articles WHERE "
        + " AND ".join(where)
        + " ORDER BY domain, id"
    )
    if limit:
        sql += " LIMIT ?"
        params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    return [
        {"id": r[0], "url": r[1], "domain": r[2], "title": r[3], "category": r[4] or ""}
        for r in rows
    ]


def apply_results(
    conn: sqlite3.Connection,
    candidates: list[dict],
    results: list[ExtractResult],
    dry_run: bool,
) -> tuple[int, int]:
    """Write files and update the database. Returns (written, updated)."""
    now = datetime.now()
    written = 0
    updated = 0

    for cand, res in zip(candidates, results):
        if not res.success:
            # Record the failure reason so the next run knows what to expect.
            if not dry_run:
                conn.execute(
                    "UPDATE articles SET content_status = ?, http_status = ?, "
                    "error_message = ? WHERE id = ?",
                    (
                        res.content_status,
                        res.status_code,
                        res.error[:500],
                        cand["id"],
                    ),
                )
            continue

        path = fulltext_path_for(cand["url"], now)
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                render_fulltext(res, cand["category"], now), encoding="utf-8"
            )

        abstract = res.markdown[:500] + "..." if len(res.markdown) > 500 else res.markdown
        if not dry_run:
            conn.execute(
                "UPDATE articles SET fulltext_path = ?, word_count = ?, "
                "content_status = 'success', http_status = ?, abstract = ?, "
                "content_hash = ?, error_message = NULL WHERE id = ?",
                (
                    str(path),
                    res.word_count,
                    res.status_code,
                    abstract,
                    content_hash(res.markdown),
                    cand["id"],
                ),
            )
        written += 1
        updated += 1

    if not dry_run:
        conn.commit()
    return written, updated


async def run(args: argparse.Namespace) -> int:
    if not DB_FILE.exists():
        print(f"ERROR: database not found: {DB_FILE}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(DB_FILE)
    try:
        candidates = fetch_candidates(
            conn, args.limit, args.domain, args.include_missing_words,
            args.include_terminal,
        )
    finally:
        conn.close()

    if not candidates:
        print("Nothing to backfill — no candidates matched.")
        return 0

    by_domain: dict[str, int] = {}
    for c in candidates:
        by_domain[c["domain"]] = by_domain.get(c["domain"], 0) + 1

    print(f"Kandidaten: {len(candidates)}")
    for dom, n in sorted(by_domain.items(), key=lambda kv: -kv[1]):
        print(f"  {dom:40s} {n}")
    print()

    if args.dry_run:
        print("DRY-RUN — nichts wird geschrieben. Verifiziere die URL-Erreichbarkeit:")
        probe = BatchScraper(
            max_concurrency=args.concurrency,
            per_domain_concurrency=args.per_domain_concurrency,
            per_domain_delay=args.per_domain_delay,
            respect_robots=not args.ignore_robots,
        )
        sample = candidates[: args.probe]
        results = await probe.scrape_many([c["url"] for c in sample])
        for cand, res in zip(sample, results):
            mark = "OK " if res.success else "FAIL"
            print(f"  {mark} {str(res.status_code or '-'):>4s} {res.word_count:>6d}w  {c['url'][:72]}")
        print()
        print(f"Probe: {probe.last_stats.summary()}")
        print(f"Gesamt-Kandidaten: {len(candidates)} | Probe: {len(sample)}")
        print("Mit --apply wird tatsächlich geschrieben.")
        return 0

    scraper = BatchScraper(
        max_concurrency=args.concurrency,
        per_domain_concurrency=args.per_domain_concurrency,
        per_domain_delay=args.per_domain_delay,
        respect_robots=not args.ignore_robots,
    )

    # In Chunks arbeiten: nach jedem Chunk wird committet. Bricht der Lauf ab
    # (Restart, Timeout), ist der Fortschritt trotzdem erhalten und der
    # naechste Lauf setzt auf dem Rest auf.
    chunk_size = max(args.chunk_size, 1)
    total_written = 0
    total_failed = 0
    status_counter: dict[str, int] = {}
    error_sample: list[tuple[str, str]] = []

    for start in range(0, len(candidates), chunk_size):
        chunk = candidates[start : start + chunk_size]
        results = await scraper.scrape_many([c["url"] for c in chunk])

        conn = sqlite3.connect(DB_FILE)
        try:
            written, _ = apply_results(conn, chunk, results, dry_run=False)
        finally:
            conn.close()

        total_written += written
        stats = scraper.last_stats
        total_failed += stats.failed
        for k, v in stats.by_status.items():
            status_counter[k] = status_counter.get(k, 0) + v
        for url, err in stats.errors.items():
            if len(error_sample) < 20:
                error_sample.append((err, url))

        done = min(start + chunk_size, len(candidates))
        print(
            f"[{done}/{len(candidates)}] geschrieben={total_written} "
            f"fehlgeschlagen={total_failed} ({stats.summary()})",
            flush=True,
        )

    print()
    print(f"Ergebnis: {total_written}/{len(candidates)} Volltexte geschrieben")
    print(f"Status:   {status_counter}")
    if error_sample:
        print("Fehler (erste 10):")
        for err, url in error_sample[:10]:
            print(f"  {err[:60]:60s} {url[:70]}")
    return 0 if total_failed == 0 else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Schreib Dateien und DB (Default: Dry-Run)")
    parser.add_argument("--limit", type=int, default=None, help="Max. Anzahl Kandidaten")
    parser.add_argument("--domain", action="append", default=[], help="Nur diese Domain (wiederholbar)")
    parser.add_argument(
        "--include-missing-words",
        action="store_true",
        help="Auch Artikel mit fulltext_path, aber word_count=0",
    )
    parser.add_argument(
        "--include-terminal",
        action="store_true",
        help="Auch Artikel mit Endstatus (paywall/blocked/410) erneut versuchen",
    )
    parser.add_argument("--concurrency", type=int, default=12)
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50,
        help="Kandidaten pro Chunk (Commit-Grenze — Fortschritt bleibt erhalten)",
    )
    parser.add_argument("--per-domain-concurrency", type=int, default=2)
    parser.add_argument("--per-domain-delay", type=float, default=1.0)
    parser.add_argument("--ignore-robots", action="store_true", help="robots.txt ignorieren")
    parser.add_argument("--probe", type=int, default=10, help="Sample-Größe im Dry-Run")
    args = parser.parse_args(argv)

    args.dry_run = not args.apply
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
