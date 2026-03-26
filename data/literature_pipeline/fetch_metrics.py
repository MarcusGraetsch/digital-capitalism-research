#!/usr/bin/env python3
"""Fetch citation metrics from OpenAlex and Semantic Scholar.

Enriches persons and works tables with citation counts, h-index, and
other bibliometric data. OpenAlex is the primary source; Semantic Scholar
is used as fallback when OpenAlex has no match.

Usage:
    python -m literature_pipeline.fetch_metrics                  # Update all stale
    python -m literature_pipeline.fetch_metrics --full           # Force-refresh everything
    python -m literature_pipeline.fetch_metrics --person-id 3    # Single person
    python -m literature_pipeline.fetch_metrics --work-id 5      # Single work
    python -m literature_pipeline.fetch_metrics --dry-run        # Preview without writing
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timedelta
from urllib.parse import quote

import requests

from .db import get_connection, init_db
from .utils import setup_logging, logger

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OPENALEX_BASE = "https://api.openalex.org"
S2_BASE = "https://api.semanticscholar.org/graph/v1"

# Polite pool: OpenAlex gives faster responses with a mailto
OPENALEX_EMAIL = os.environ.get("OPENALEX_EMAIL", "marcusgraetsch@gmail.com")

# How old metrics can be before we refresh (days)
STALE_THRESHOLD_DAYS = 90

# Rate limiting
OPENALEX_DELAY = 0.15   # ~6 req/s (well within free tier)
S2_DELAY = 3.5          # 100 req/5min = ~0.33/s, be conservative


def _openalex_headers():
    return {"User-Agent": f"mailto:{OPENALEX_EMAIL}"}


def _s2_headers():
    key = os.environ.get("S2_API_KEY")
    if key:
        return {"x-api-key": key}
    return {}


# ---------------------------------------------------------------------------
# OpenAlex: Author lookup
# ---------------------------------------------------------------------------

def openalex_fetch_author_by_id(openalex_id):
    """Fetch author by OpenAlex ID (e.g. 'A5073480907')."""
    # Normalize ID format
    if not openalex_id.startswith("https://"):
        openalex_id = f"https://openalex.org/authors/{openalex_id}"

    url = f"{OPENALEX_BASE}/authors/{openalex_id}"
    try:
        resp = requests.get(url, headers=_openalex_headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException as e:
        logger.debug(f"OpenAlex author fetch failed: {e}")
    return None


def openalex_search_author(name):
    """Search OpenAlex for an author by name."""
    url = f"{OPENALEX_BASE}/authors"
    params = {"search": name, "per_page": 5}
    try:
        resp = requests.get(url, params=params, headers=_openalex_headers(), timeout=15)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                # Return best match (first result, highest relevance)
                return results[0]
    except requests.RequestException as e:
        logger.debug(f"OpenAlex author search failed: {e}")
    return None


def _extract_openalex_author_metrics(data):
    """Extract metrics dict from OpenAlex author response."""
    if not data:
        return None
    stats = data.get("summary_stats", {})
    return {
        "works_count": data.get("works_count"),
        "cited_by_count": data.get("cited_by_count"),
        "h_index": stats.get("h_index"),
        "i10_index": stats.get("i10_index"),
        "mean_citedness_2yr": stats.get("2yr_mean_citedness"),
        "openalex_id": data.get("id", "").replace("https://openalex.org/authors/", ""),
    }


# ---------------------------------------------------------------------------
# OpenAlex: Work lookup
# ---------------------------------------------------------------------------

def openalex_search_work(title, year=None):
    """Search OpenAlex for a work by title (and optionally year)."""
    url = f"{OPENALEX_BASE}/works"
    params = {"search": title, "per_page": 5}
    if year:
        params["filter"] = f"publication_year:{year}"
    try:
        resp = requests.get(url, params=params, headers=_openalex_headers(), timeout=15)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]
    except requests.RequestException as e:
        logger.debug(f"OpenAlex work search failed: {e}")
    return None


def openalex_fetch_work_by_doi(doi):
    """Fetch work by DOI."""
    url = f"{OPENALEX_BASE}/works/doi:{doi}"
    try:
        resp = requests.get(url, headers=_openalex_headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException as e:
        logger.debug(f"OpenAlex work DOI fetch failed: {e}")
    return None


def _extract_openalex_work_metrics(data):
    """Extract metrics dict from OpenAlex work response."""
    if not data:
        return None
    return {
        "cited_by_count": data.get("cited_by_count"),
        "citation_percentile": (data.get("citation_normalized_percentile") or {}).get("value"),
        "fwci": data.get("fwci"),
        "openalex_id": data.get("id", "").replace("https://openalex.org/works/", ""),
    }


# ---------------------------------------------------------------------------
# Semantic Scholar: Fallback
# ---------------------------------------------------------------------------

def s2_search_author(name):
    """Search Semantic Scholar for an author."""
    url = f"{S2_BASE}/author/search"
    params = {"query": name, "limit": 3, "fields": "name,hIndex,citationCount,paperCount"}
    try:
        resp = requests.get(url, params=params, headers=_s2_headers(), timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data:
                return data[0]
    except requests.RequestException as e:
        logger.debug(f"S2 author search failed: {e}")
    return None


def _extract_s2_author_metrics(data):
    """Extract metrics dict from Semantic Scholar author response."""
    if not data:
        return None
    return {
        "works_count": data.get("paperCount"),
        "cited_by_count": data.get("citationCount"),
        "h_index": data.get("hIndex"),
        "s2_id": str(data.get("authorId", "")),
    }


def s2_search_work(title):
    """Search Semantic Scholar for a work by title."""
    url = f"{S2_BASE}/paper/search"
    params = {
        "query": title,
        "limit": 3,
        "fields": "title,citationCount,influentialCitationCount,year",
    }
    try:
        resp = requests.get(url, params=params, headers=_s2_headers(), timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            if data:
                return data[0]
    except requests.RequestException as e:
        logger.debug(f"S2 work search failed: {e}")
    return None


def _extract_s2_work_metrics(data):
    """Extract metrics dict from Semantic Scholar work response."""
    if not data:
        return None
    return {
        "cited_by_count": data.get("citationCount"),
        "influential_citations": data.get("influentialCitationCount"),
        "s2_id": data.get("paperId", ""),
    }


# ---------------------------------------------------------------------------
# Core: Fetch & Store for a single person
# ---------------------------------------------------------------------------

def fetch_person_metrics(conn, person_id, force=False):
    """Fetch and store citation metrics for a person.

    Returns True if metrics were updated, False otherwise.
    """
    person = conn.execute("SELECT * FROM persons WHERE id = ?", (person_id,)).fetchone()
    if not person or person["merged_into_id"]:
        return False

    # Check staleness
    if not force and person["metrics_updated_at"]:
        updated = datetime.fromisoformat(person["metrics_updated_at"])
        if datetime.now() - updated < timedelta(days=STALE_THRESHOLD_DAYS):
            return False

    name = person["display_name"] or person["canonical_name"]
    logger.info(f"  Fetching metrics for: {name}")

    # Try OpenAlex first
    metrics = None
    source = None

    # Check if we have an OpenAlex ID stored
    ext = conn.execute(
        "SELECT external_id FROM person_external_ids WHERE person_id = ? AND id_type = 'openalex'",
        (person_id,),
    ).fetchone()

    if ext:
        data = openalex_fetch_author_by_id(ext["external_id"])
        metrics = _extract_openalex_author_metrics(data)
        if metrics:
            source = "openalex"
        time.sleep(OPENALEX_DELAY)

    if not metrics:
        # Search by name
        data = openalex_search_author(name)
        metrics = _extract_openalex_author_metrics(data)
        if metrics:
            source = "openalex"
            # Store the discovered OpenAlex ID
            if metrics.get("openalex_id"):
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO person_external_ids
                           (person_id, id_type, external_id, created_at)
                           VALUES (?, 'openalex', ?, ?)""",
                        (person_id, metrics["openalex_id"], datetime.now().isoformat()),
                    )
                except Exception:
                    pass
        time.sleep(OPENALEX_DELAY)

    # Fallback to Semantic Scholar
    if not metrics:
        data = s2_search_author(name)
        metrics = _extract_s2_author_metrics(data)
        if metrics:
            source = "semantic_scholar"
            if metrics.get("s2_id"):
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO person_external_ids
                           (person_id, id_type, external_id, created_at)
                           VALUES (?, 's2', ?, ?)""",
                        (person_id, metrics["s2_id"], datetime.now().isoformat()),
                    )
                except Exception:
                    pass
        time.sleep(S2_DELAY)

    if not metrics:
        logger.debug(f"  No metrics found for: {name}")
        # Still update timestamp so we don't retry too soon
        conn.execute(
            "UPDATE persons SET metrics_updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), person_id),
        )
        conn.commit()
        return False

    # Store metrics
    now = datetime.now().isoformat()
    conn.execute(
        """UPDATE persons SET
           works_count = COALESCE(?, works_count),
           cited_by_count = COALESCE(?, cited_by_count),
           h_index = COALESCE(?, h_index),
           i10_index = COALESCE(?, i10_index),
           mean_citedness_2yr = COALESCE(?, mean_citedness_2yr),
           metrics_source = ?,
           metrics_updated_at = ?,
           updated_at = ?
           WHERE id = ?""",
        (
            metrics.get("works_count"),
            metrics.get("cited_by_count"),
            metrics.get("h_index"),
            metrics.get("i10_index"),
            metrics.get("mean_citedness_2yr"),
            source,
            now, now,
            person_id,
        ),
    )
    conn.commit()

    cited = metrics.get("cited_by_count") or 0
    h = metrics.get("h_index") or 0
    logger.info(f"    [{source}] cited_by={cited}, h_index={h}")
    return True


# ---------------------------------------------------------------------------
# Core: Fetch & Store for a single work
# ---------------------------------------------------------------------------

def fetch_work_metrics(conn, work_id, force=False):
    """Fetch and store citation metrics for a work.

    Returns True if metrics were updated, False otherwise.
    """
    work = conn.execute("SELECT * FROM works WHERE id = ?", (work_id,)).fetchone()
    if not work or work["merged_into_id"]:
        return False

    # Check staleness
    if not force and work["metrics_updated_at"]:
        updated = datetime.fromisoformat(work["metrics_updated_at"])
        if datetime.now() - updated < timedelta(days=STALE_THRESHOLD_DAYS):
            return False

    title = work["canonical_title"]
    logger.info(f"  Fetching metrics for work: {title[:60]}")

    metrics = None
    source = None

    # Check for DOI in work_external_ids
    doi_row = conn.execute(
        "SELECT external_id FROM work_external_ids WHERE work_id = ? AND id_type = 'doi'",
        (work_id,),
    ).fetchone()

    if doi_row:
        data = openalex_fetch_work_by_doi(doi_row["external_id"])
        metrics = _extract_openalex_work_metrics(data)
        if metrics:
            source = "openalex"
        time.sleep(OPENALEX_DELAY)

    # Also check the linked source for DOI
    if not metrics and work["source_id"]:
        src = conn.execute(
            "SELECT doi FROM sources WHERE id = ?", (work["source_id"],)
        ).fetchone()
        if src and src["doi"]:
            data = openalex_fetch_work_by_doi(src["doi"])
            metrics = _extract_openalex_work_metrics(data)
            if metrics:
                source = "openalex"
            time.sleep(OPENALEX_DELAY)

    if not metrics:
        # Search by title + year
        data = openalex_search_work(title, year=work["year"])
        metrics = _extract_openalex_work_metrics(data)
        if metrics:
            source = "openalex"
            if metrics.get("openalex_id"):
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO work_external_ids
                           (work_id, id_type, external_id, created_at)
                           VALUES (?, 'openalex', ?, ?)""",
                        (work_id, metrics["openalex_id"], datetime.now().isoformat()),
                    )
                except Exception:
                    pass
        time.sleep(OPENALEX_DELAY)

    # Fallback to Semantic Scholar
    if not metrics:
        data = s2_search_work(title)
        s2_metrics = _extract_s2_work_metrics(data)
        if s2_metrics:
            metrics = s2_metrics
            source = "semantic_scholar"
            if metrics.get("s2_id"):
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO work_external_ids
                           (work_id, id_type, external_id, created_at)
                           VALUES (?, 's2', ?, ?)""",
                        (work_id, metrics["s2_id"], datetime.now().isoformat()),
                    )
                except Exception:
                    pass
        time.sleep(S2_DELAY)

    if not metrics:
        logger.debug(f"  No metrics found for work: {title[:60]}")
        conn.execute(
            "UPDATE works SET metrics_updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), work_id),
        )
        conn.commit()
        return False

    now = datetime.now().isoformat()
    conn.execute(
        """UPDATE works SET
           cited_by_count = COALESCE(?, cited_by_count),
           influential_citations = COALESCE(?, influential_citations),
           citation_percentile = COALESCE(?, citation_percentile),
           fwci = COALESCE(?, fwci),
           metrics_source = ?,
           metrics_updated_at = ?,
           updated_at = ?
           WHERE id = ?""",
        (
            metrics.get("cited_by_count"),
            metrics.get("influential_citations"),
            metrics.get("citation_percentile"),
            metrics.get("fwci"),
            source,
            now, now,
            work_id,
        ),
    )
    conn.commit()

    cited = metrics.get("cited_by_count") or 0
    logger.info(f"    [{source}] cited_by={cited}")
    return True


# ---------------------------------------------------------------------------
# Inline fetch: called from pipelines for newly created persons/works
# ---------------------------------------------------------------------------

def fetch_metrics_for_new_person(conn, person_id):
    """Non-blocking metrics fetch for a newly created person.

    Called inline from pipelines. Logs but doesn't raise on failure.
    """
    try:
        fetch_person_metrics(conn, person_id, force=True)
    except Exception as e:
        logger.debug(f"Inline person metrics fetch failed: {e}")


def fetch_metrics_for_new_work(conn, work_id):
    """Non-blocking metrics fetch for a newly created work.

    Called inline from pipelines. Logs but doesn't raise on failure.
    """
    try:
        fetch_work_metrics(conn, work_id, force=True)
    except Exception as e:
        logger.debug(f"Inline work metrics fetch failed: {e}")


# ---------------------------------------------------------------------------
# Batch: Update all persons and works
# ---------------------------------------------------------------------------

def update_all_persons(conn, force=False, dry_run=False):
    """Fetch metrics for all persons that need updating."""
    if force:
        rows = conn.execute(
            "SELECT id, display_name, canonical_name FROM persons WHERE merged_into_id IS NULL"
        ).fetchall()
    else:
        cutoff = (datetime.now() - timedelta(days=STALE_THRESHOLD_DAYS)).isoformat()
        rows = conn.execute(
            """SELECT id, display_name, canonical_name FROM persons
               WHERE merged_into_id IS NULL
                 AND (metrics_updated_at IS NULL OR metrics_updated_at < ?)""",
            (cutoff,),
        ).fetchall()

    logger.info(f"Persons to update: {len(rows)}")
    updated = 0

    for row in rows:
        name = row["display_name"] or row["canonical_name"]
        if dry_run:
            logger.info(f"  [dry-run] Would fetch: {name}")
            continue
        if fetch_person_metrics(conn, row["id"], force=force):
            updated += 1

    logger.info(f"Persons updated: {updated}/{len(rows)}")
    return updated


def update_all_works(conn, force=False, dry_run=False):
    """Fetch metrics for all works that need updating."""
    if force:
        rows = conn.execute(
            "SELECT id, canonical_title FROM works WHERE merged_into_id IS NULL"
        ).fetchall()
    else:
        cutoff = (datetime.now() - timedelta(days=STALE_THRESHOLD_DAYS)).isoformat()
        rows = conn.execute(
            """SELECT id, canonical_title FROM works
               WHERE merged_into_id IS NULL
                 AND (metrics_updated_at IS NULL OR metrics_updated_at < ?)""",
            (cutoff,),
        ).fetchall()

    logger.info(f"Works to update: {len(rows)}")
    updated = 0

    for row in rows:
        if dry_run:
            logger.info(f"  [dry-run] Would fetch: {row['canonical_title'][:60]}")
            continue
        if fetch_work_metrics(conn, row["id"], force=force):
            updated += 1

    logger.info(f"Works updated: {updated}/{len(rows)}")
    return updated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Fetch citation metrics from OpenAlex / Semantic Scholar"
    )
    parser.add_argument("--full", action="store_true", help="Force-refresh all, ignore staleness")
    parser.add_argument("--persons-only", action="store_true", help="Only update persons")
    parser.add_argument("--works-only", action="store_true", help="Only update works")
    parser.add_argument("--person-id", type=int, help="Update a single person")
    parser.add_argument("--work-id", type=int, help="Update a single work")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    conn = init_db()

    if args.person_id:
        fetch_person_metrics(conn, args.person_id, force=True)
    elif args.work_id:
        fetch_work_metrics(conn, args.work_id, force=True)
    else:
        if not args.works_only:
            logger.info("=== Fetching person metrics ===")
            update_all_persons(conn, force=args.full, dry_run=args.dry_run)

        if not args.persons_only:
            logger.info("=== Fetching work metrics ===")
            update_all_works(conn, force=args.full, dry_run=args.dry_run)

    # Print summary
    p_with = conn.execute(
        "SELECT COUNT(*) FROM persons WHERE cited_by_count IS NOT NULL AND merged_into_id IS NULL"
    ).fetchone()[0]
    p_total = conn.execute(
        "SELECT COUNT(*) FROM persons WHERE merged_into_id IS NULL"
    ).fetchone()[0]
    w_with = conn.execute(
        "SELECT COUNT(*) FROM works WHERE cited_by_count IS NOT NULL AND merged_into_id IS NULL"
    ).fetchone()[0]
    w_total = conn.execute(
        "SELECT COUNT(*) FROM works WHERE merged_into_id IS NULL"
    ).fetchone()[0]

    logger.info(f"\nMetrics coverage: {p_with}/{p_total} persons, {w_with}/{w_total} works")
    conn.close()


if __name__ == "__main__":
    main()
