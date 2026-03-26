#!/usr/bin/env python3
"""Literature Discovery Pipeline — snowball sampling from seed works/persons.

Discovers new relevant works via citation chasing, author exploration,
web search, and Semantic Scholar recommendations. Scores candidates
with LLM and queues them for human review.

Usage:
    python3 discover_literature.py                    # Full discovery run
    python3 discover_literature.py --strategy refs    # Only reference chasing
    python3 discover_literature.py --strategy web     # Only web search
    python3 discover_literature.py --review           # Show pending candidates
    python3 discover_literature.py --accept ID [ID..] # Accept candidates
    python3 discover_literature.py --reject ID [ID..] # Reject candidates
    python3 discover_literature.py --stats            # Discovery stats
    python3 discover_literature.py --dry-run          # Preview without storing
    python3 discover_literature.py --limit 5          # Limit candidates per strategy
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

from literature_pipeline.db import get_connection, init_db, _normalize_title
from literature_pipeline.llm_backend import LLMBackend
from literature_pipeline.utils import setup_logging, logger

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OPENALEX_BASE = "https://api.openalex.org"
S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_REC_BASE = "https://api.semanticscholar.org/recommendations/v1"

OPENALEX_EMAIL = os.environ.get("OPENALEX_EMAIL", "marcusgraetsch@gmail.com")
OPENALEX_DELAY = 0.15
S2_DELAY = 3.5

REPORT_DIR = Path(__file__).parent / "discovery-reports"

STRATEGIES = ["refs", "cites", "author_works", "web", "s2_recommendations"]

# Research themes for LLM scoring context
RESEARCH_THEMES = """
This research project investigates digital capitalism through Marxist political economy.
Core themes: platform capitalism, surveillance capitalism, data extractivism,
digital labor, algorithmic management, monopoly/concentration in tech,
financialization of tech, gig economy, AI and automation, tech imperialism,
digital colonialism, data as commodity, network effects and rent-seeking,
political economy of social media, tech worker organizing.
Key theorists include: Marx, Zuboff, Srnicek, Morozov, Fuchs, Couldry & Mejias,
Mezzadra & Neilson, Pasquale, Noble, Eubanks, Crawford, Sadowski, Staab.
"""


def _openalex_headers():
    return {"User-Agent": f"mailto:{OPENALEX_EMAIL}"}


def _s2_headers():
    key = os.environ.get("S2_API_KEY")
    if key:
        return {"x-api-key": key}
    return {}


def _openalex_get(endpoint, params=None):
    """Make an OpenAlex API request. Returns JSON dict or None."""
    url = f"{OPENALEX_BASE}{endpoint}"
    if params is None:
        params = {}
    params["mailto"] = OPENALEX_EMAIL
    try:
        resp = requests.get(url, params=params, headers=_openalex_headers(), timeout=20)
        if resp.status_code == 200:
            return resp.json()
        logger.debug(f"OpenAlex {resp.status_code}: {endpoint}")
    except requests.RequestException as e:
        logger.debug(f"OpenAlex error: {e}")
    return None


def _s2_get(endpoint, params=None):
    """Make a Semantic Scholar API request. Returns JSON dict or None."""
    url = f"{S2_BASE}{endpoint}"
    try:
        resp = requests.get(url, params=params or {}, headers=_s2_headers(), timeout=20)
        if resp.status_code == 200:
            return resp.json()
        logger.debug(f"S2 {resp.status_code}: {endpoint}")
    except requests.RequestException as e:
        logger.debug(f"S2 error: {e}")
    return None


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
        return " ".join(word for _, word in word_positions)
    except Exception:
        return None


def _parse_openalex_work(work):
    """Parse an OpenAlex work object into a candidate dict."""
    openalex_id = work.get("id", "").replace("https://openalex.org/", "")

    authorships = work.get("authorships", [])
    authors = [a.get("author", {}).get("display_name", "") for a in authorships]
    authors = [a for a in authors if a]

    source = work.get("primary_location", {}) or {}
    source_obj = source.get("source", {}) or {}
    journal = source_obj.get("display_name", "")

    oa_url = None
    oa = work.get("open_access", {}) or {}
    oa_url = oa.get("oa_url")
    if not oa_url:
        best_loc = work.get("best_oa_location", {}) or {}
        oa_url = best_loc.get("pdf_url") or best_loc.get("landing_page_url")

    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

    doi = work.get("doi")
    if doi and doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")

    return {
        "title": work.get("title") or "Untitled",
        "authors": json.dumps(authors),
        "year": work.get("publication_year"),
        "abstract": abstract,
        "doi": doi,
        "openalex_id": openalex_id,
        "open_access_url": oa_url,
        "journal": journal,
        "cited_by_count": work.get("cited_by_count", 0),
    }


def _title_hash(title):
    """Normalize and hash a title for dedup."""
    norm = _normalize_title(title)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def dedup_candidate(conn, candidate):
    """Check if this candidate already exists in discovery_queue or works.
    Returns True if it's a duplicate (should be skipped).
    """
    th = _title_hash(candidate["title"])

    # Check discovery_queue
    row = conn.execute(
        "SELECT id FROM discovery_queue WHERE title_hash = ?", (th,)
    ).fetchone()
    if row:
        return True

    # Check existing works table
    sort = _normalize_title(candidate["title"])
    if candidate.get("year"):
        row = conn.execute(
            "SELECT id FROM works WHERE sort_title = ? AND year = ? AND merged_into_id IS NULL",
            (sort, candidate["year"]),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM works WHERE sort_title = ? AND merged_into_id IS NULL",
            (sort,),
        ).fetchone()
    if row:
        return True

    # Check sources table
    row = conn.execute(
        "SELECT id FROM sources WHERE LOWER(title) = LOWER(?)", (candidate["title"],)
    ).fetchone()
    if row:
        return True

    return False


# ---------------------------------------------------------------------------
# Strategy 1: References of seed works (backward citation chasing)
# ---------------------------------------------------------------------------

def discover_from_references(conn, limit=20):
    """For each work with an OpenAlex ID, fetch its referenced_works."""
    candidates = []

    # Get works with OpenAlex IDs
    rows = conn.execute("""
        SELECT w.id, w.canonical_title, wei.external_id as openalex_id
        FROM works w
        JOIN work_external_ids wei ON wei.work_id = w.id AND wei.id_type = 'openalex'
        WHERE w.merged_into_id IS NULL
        ORDER BY w.cited_by_count DESC NULLS LAST
    """).fetchall()

    logger.info(f"  [refs] {len(rows)} seed works with OpenAlex IDs")

    for row in rows:
        if len(candidates) >= limit:
            break

        oa_id = row["openalex_id"]
        work_id = row["id"]
        logger.debug(f"  Fetching refs for: {row['canonical_title'][:50]}")

        data = _openalex_get(f"/works/{oa_id}")
        time.sleep(OPENALEX_DELAY)

        if not data:
            continue

        ref_ids = data.get("referenced_works", [])
        if not ref_ids:
            continue

        # Fetch referenced works in batches via filter
        # OpenAlex supports pipe-separated IDs
        batch_size = 25
        for i in range(0, min(len(ref_ids), 100), batch_size):
            if len(candidates) >= limit:
                break

            batch = ref_ids[i:i + batch_size]
            id_filter = "|".join(
                rid.replace("https://openalex.org/", "") for rid in batch
            )
            batch_data = _openalex_get("/works", {
                "filter": f"openalex:{id_filter}",
                "per_page": batch_size,
            })
            time.sleep(OPENALEX_DELAY)

            if not batch_data:
                continue

            for work in batch_data.get("results", []):
                if len(candidates) >= limit:
                    break
                cand = _parse_openalex_work(work)
                cand["discovered_via"] = f"refs_of:{oa_id}"
                cand["discovered_from_work_id"] = work_id
                if not dedup_candidate(conn, cand):
                    cand["title_hash"] = _title_hash(cand["title"])
                    candidates.append(cand)

    logger.info(f"  [refs] {len(candidates)} new candidates")
    return candidates


# ---------------------------------------------------------------------------
# Strategy 2: Citing works (forward citation chasing)
# ---------------------------------------------------------------------------

def discover_from_citations(conn, limit=20):
    """For high-cited seed works, fetch works that cite them."""
    candidates = []

    rows = conn.execute("""
        SELECT w.id, w.canonical_title, w.cited_by_count,
               wei.external_id as openalex_id
        FROM works w
        JOIN work_external_ids wei ON wei.work_id = w.id AND wei.id_type = 'openalex'
        WHERE w.merged_into_id IS NULL
          AND w.cited_by_count IS NOT NULL
          AND w.cited_by_count > 10
        ORDER BY w.cited_by_count DESC
        LIMIT 10
    """).fetchall()

    logger.info(f"  [cites] {len(rows)} high-cited seed works to check")

    for row in rows:
        if len(candidates) >= limit:
            break

        oa_id = row["openalex_id"]
        work_id = row["id"]

        data = _openalex_get("/works", {
            "filter": f"cites:{oa_id}",
            "sort": "cited_by_count:desc",
            "per_page": 10,
        })
        time.sleep(OPENALEX_DELAY)

        if not data:
            continue

        for work in data.get("results", []):
            if len(candidates) >= limit:
                break
            cand = _parse_openalex_work(work)
            cand["discovered_via"] = f"cites:{oa_id}"
            cand["discovered_from_work_id"] = work_id
            if not dedup_candidate(conn, cand):
                cand["title_hash"] = _title_hash(cand["title"])
                candidates.append(cand)

    logger.info(f"  [cites] {len(candidates)} new candidates")
    return candidates


# ---------------------------------------------------------------------------
# Strategy 3: Other works by seed persons
# ---------------------------------------------------------------------------

def discover_author_works(conn, limit=20):
    """For each seed person with OpenAlex ID, fetch their full works list."""
    candidates = []

    rows = conn.execute("""
        SELECT p.id, p.display_name, p.canonical_name,
               pei.external_id as openalex_id
        FROM persons p
        JOIN person_external_ids pei ON pei.person_id = p.id AND pei.id_type = 'openalex'
        WHERE p.is_seed = 1 AND p.merged_into_id IS NULL
    """).fetchall()

    logger.info(f"  [author_works] {len(rows)} seed persons with OpenAlex IDs")

    for row in rows:
        if len(candidates) >= limit:
            break

        oa_id = row["openalex_id"]
        person_id = row["id"]
        name = row["display_name"] or row["canonical_name"]

        data = _openalex_get("/works", {
            "filter": f"author.id:{oa_id},type:book|article|book-chapter",
            "sort": "cited_by_count:desc",
            "per_page": 15,
        })
        time.sleep(OPENALEX_DELAY)

        if not data:
            continue

        for work in data.get("results", []):
            if len(candidates) >= limit:
                break
            cand = _parse_openalex_work(work)
            cand["discovered_via"] = f"author:{oa_id}"
            cand["discovered_from_person_id"] = person_id
            if not dedup_candidate(conn, cand):
                cand["title_hash"] = _title_hash(cand["title"])
                candidates.append(cand)

    logger.info(f"  [author_works] {len(candidates)} new candidates")
    return candidates


# ---------------------------------------------------------------------------
# Strategy 4: Web search (Semantic Scholar keyword search as fallback)
# ---------------------------------------------------------------------------

def discover_web_search(conn, limit=10):
    """Build targeted queries from seed persons + research concepts.

    Uses Semantic Scholar keyword search (free, no API key needed).
    Falls back gracefully if API is down.
    """
    candidates = []

    # Build queries from seed persons + themes
    seed_persons = conn.execute("""
        SELECT display_name, canonical_name FROM persons
        WHERE is_seed = 1 AND merged_into_id IS NULL
        ORDER BY RANDOM() LIMIT 3
    """).fetchall()

    themes = [
        "digital capitalism",
        "platform capitalism",
        "surveillance capitalism",
        "data extractivism",
        "digital labor exploitation",
    ]

    queries = []
    for person in seed_persons:
        name = person["display_name"] or person["canonical_name"]
        # Pick a random theme to pair
        import random
        theme = random.choice(themes)
        queries.append(f"{name} {theme}")

    # Also add 2 pure theme queries
    queries.extend(random.sample(themes, min(2, len(themes))))

    logger.info(f"  [web] Running {len(queries)} search queries")

    for query in queries[:5]:
        if len(candidates) >= limit:
            break

        logger.debug(f"  S2 search: {query}")
        data = _s2_get("/paper/search", {
            "query": query,
            "limit": 5,
            "fields": "title,authors,year,abstract,externalIds,citationCount,journal,openAccessPdf",
        })
        time.sleep(S2_DELAY)

        if not data:
            continue

        for paper in data.get("data", []) or []:
            if len(candidates) >= limit:
                break

            title = paper.get("title")
            if not title:
                continue

            ext_ids = paper.get("externalIds") or {}
            authors = [a.get("name", "") for a in (paper.get("authors") or [])]

            journal_info = paper.get("journal") or {}
            journal_name = journal_info.get("name", "") if isinstance(journal_info, dict) else ""

            oa_pdf = paper.get("openAccessPdf") or {}
            oa_url = oa_pdf.get("url") if isinstance(oa_pdf, dict) else None

            cand = {
                "title": title,
                "authors": json.dumps([a for a in authors if a]),
                "year": paper.get("year"),
                "abstract": paper.get("abstract"),
                "doi": ext_ids.get("DOI"),
                "openalex_id": ext_ids.get("CorpusId"),
                "s2_id": paper.get("paperId"),
                "open_access_url": oa_url,
                "journal": journal_name,
                "cited_by_count": paper.get("citationCount", 0),
                "discovered_via": f"web:{query}",
            }

            if not dedup_candidate(conn, cand):
                cand["title_hash"] = _title_hash(cand["title"])
                candidates.append(cand)

    logger.info(f"  [web] {len(candidates)} new candidates")
    return candidates


# ---------------------------------------------------------------------------
# Strategy 5: Semantic Scholar recommendations
# ---------------------------------------------------------------------------

def discover_s2_recommendations(conn, limit=10):
    """For works with S2 IDs, use the recommendations endpoint."""
    candidates = []

    rows = conn.execute("""
        SELECT w.id, w.canonical_title, wei.external_id as s2_id
        FROM works w
        JOIN work_external_ids wei ON wei.work_id = w.id AND wei.id_type = 's2'
        WHERE w.merged_into_id IS NULL
        ORDER BY w.cited_by_count DESC NULLS LAST
        LIMIT 5
    """).fetchall()

    logger.info(f"  [s2rec] {len(rows)} seed works with S2 IDs")

    for row in rows:
        if len(candidates) >= limit:
            break

        s2_id = row["s2_id"]
        work_id = row["id"]

        url = f"{S2_REC_BASE}/papers/forpaper/{s2_id}"
        try:
            resp = requests.get(
                url,
                params={"limit": 5, "fields": "title,authors,year,abstract,externalIds,citationCount,journal,openAccessPdf"},
                headers=_s2_headers(),
                timeout=20,
            )
            if resp.status_code != 200:
                logger.debug(f"S2 recommendations {resp.status_code} for {s2_id}")
                time.sleep(S2_DELAY)
                continue
            data = resp.json()
        except requests.RequestException as e:
            logger.debug(f"S2 recommendations error: {e}")
            time.sleep(S2_DELAY)
            continue

        time.sleep(S2_DELAY)

        for paper in data.get("recommendedPapers", []):
            if len(candidates) >= limit:
                break

            title = paper.get("title")
            if not title:
                continue

            ext_ids = paper.get("externalIds") or {}
            authors = [a.get("name", "") for a in (paper.get("authors") or [])]

            journal_info = paper.get("journal") or {}
            journal_name = journal_info.get("name", "") if isinstance(journal_info, dict) else ""

            oa_pdf = paper.get("openAccessPdf") or {}
            oa_url = oa_pdf.get("url") if isinstance(oa_pdf, dict) else None

            cand = {
                "title": title,
                "authors": json.dumps([a for a in authors if a]),
                "year": paper.get("year"),
                "abstract": paper.get("abstract"),
                "doi": ext_ids.get("DOI"),
                "s2_id": paper.get("paperId"),
                "open_access_url": oa_url,
                "journal": journal_name,
                "cited_by_count": paper.get("citationCount", 0),
                "discovered_via": f"s2rec:{s2_id}",
                "discovered_from_work_id": work_id,
            }

            if not dedup_candidate(conn, cand):
                cand["title_hash"] = _title_hash(cand["title"])
                candidates.append(cand)

    logger.info(f"  [s2rec] {len(candidates)} new candidates")
    return candidates


# ---------------------------------------------------------------------------
# LLM Relevance Scoring
# ---------------------------------------------------------------------------

SCORING_SYSTEM = f"""You are an academic research assistant evaluating papers for relevance
to a research project on digital capitalism and Marxist political economy.

{RESEARCH_THEMES}

For each candidate, return a JSON object with:
- relevance (0-10): How relevant to the project's themes?
- novelty (0-10): Does this seem like a distinct contribution vs. something already covered?
- verdict: "accept" (relevance >= 7), "maybe" (4-6), "reject" (< 4)
- reasoning: One sentence explaining the verdict.
"""

SCORING_PROMPT = """Evaluate this candidate work:

Title: {title}
Authors: {authors}
Year: {year}
Journal: {journal}
Abstract: {abstract}

Return JSON: {{"relevance": N, "novelty": N, "verdict": "accept|maybe|reject", "reasoning": "..."}}"""


def score_candidate(backend, candidate):
    """Score a single candidate via LLM. Returns scoring dict."""
    authors = candidate.get("authors", "[]")
    if isinstance(authors, str):
        try:
            authors = ", ".join(json.loads(authors))
        except (json.JSONDecodeError, TypeError):
            pass

    abstract = candidate.get("abstract") or "No abstract available."
    if len(abstract) > 1000:
        abstract = abstract[:1000] + "..."

    prompt = SCORING_PROMPT.format(
        title=candidate["title"],
        authors=authors,
        year=candidate.get("year", "?"),
        journal=candidate.get("journal", "?"),
        abstract=abstract,
    )

    try:
        result = backend.complete_json(
            prompt,
            system=SCORING_SYSTEM,
            task="score_relevance",
            max_tokens=256,
            temperature=0.1,
        )
        return {
            "relevance_score": int(result.get("relevance", 0)),
            "novelty_score": int(result.get("novelty", 0)),
            "llm_verdict": result.get("verdict", "reject"),
            "llm_reasoning": result.get("reasoning", ""),
        }
    except Exception as e:
        logger.warning(f"  LLM scoring failed for '{candidate['title'][:50]}': {e}")
        return {
            "relevance_score": None,
            "novelty_score": None,
            "llm_verdict": "maybe",
            "llm_reasoning": f"Scoring failed: {e}",
        }


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def store_candidates(conn, candidates):
    """Insert scored candidates into discovery_queue. Returns count stored."""
    stored = 0
    for cand in candidates:
        # Only store accept and maybe
        verdict = cand.get("llm_verdict", "maybe")
        if verdict == "reject":
            logger.debug(f"  Skipping rejected: {cand['title'][:50]}")
            continue

        try:
            conn.execute("""
                INSERT OR IGNORE INTO discovery_queue
                (title, authors, year, abstract, doi, openalex_id, s2_id,
                 open_access_url, journal, cited_by_count,
                 discovered_via, discovered_from_work_id, discovered_from_person_id,
                 relevance_score, novelty_score, llm_verdict, llm_reasoning,
                 title_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cand["title"],
                cand.get("authors"),
                cand.get("year"),
                cand.get("abstract"),
                cand.get("doi"),
                cand.get("openalex_id"),
                cand.get("s2_id"),
                cand.get("open_access_url"),
                cand.get("journal"),
                cand.get("cited_by_count"),
                cand["discovered_via"],
                cand.get("discovered_from_work_id"),
                cand.get("discovered_from_person_id"),
                cand.get("relevance_score"),
                cand.get("novelty_score"),
                cand.get("llm_verdict"),
                cand.get("llm_reasoning"),
                cand.get("title_hash"),
            ))
            stored += 1
        except Exception as e:
            logger.debug(f"  Insert failed for '{cand['title'][:40]}': {e}")

    conn.commit()
    return stored


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(conn, candidates, output_dir=None):
    """Generate a markdown discovery report. Returns Path to report."""
    output_dir = output_dir or REPORT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    filename = f"discovery_{now.strftime('%Y%m%d')}.md"
    filepath = output_dir / filename

    accepted = [c for c in candidates if c.get("llm_verdict") == "accept"]
    maybe = [c for c in candidates if c.get("llm_verdict") == "maybe"]
    rejected = [c for c in candidates if c.get("llm_verdict") == "reject"]

    # Strategy stats
    strat_counts = {}
    for c in candidates:
        via = c.get("discovered_via", "unknown").split(":")[0]
        strat_counts[via] = strat_counts.get(via, 0) + 1

    lines = [
        f"# Literature Discovery Report — {now.strftime('%Y-%m-%d')}",
        "",
        "## Summary",
        "",
        f"- **Total candidates found:** {len(candidates)}",
        f"- **Accepted:** {len(accepted)}",
        f"- **Maybe:** {len(maybe)}",
        f"- **Rejected:** {len(rejected)}",
        "",
    ]

    if accepted:
        lines.append("## Accepted Candidates (relevance >= 7)")
        lines.append("")
        lines.append("| # | Title | Authors | Year | Relevance | Novelty | Discovered Via | Reasoning |")
        lines.append("|---|-------|---------|------|-----------|---------|----------------|-----------|")
        for i, c in enumerate(accepted, 1):
            authors = c.get("authors", "[]")
            if isinstance(authors, str):
                try:
                    authors = ", ".join(json.loads(authors)[:2])
                except (json.JSONDecodeError, TypeError):
                    pass
            if len(authors) > 40:
                authors = authors[:37] + "..."
            title = c["title"]
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(
                f"| {i} | {title} | {authors} | {c.get('year', '?')} | "
                f"{c.get('relevance_score', '?')} | {c.get('novelty_score', '?')} | "
                f"{c.get('discovered_via', '?')} | {c.get('llm_reasoning', '')} |"
            )
        lines.append("")

    if maybe:
        lines.append("## Maybe Candidates (relevance 4-6)")
        lines.append("")
        lines.append("| # | Title | Authors | Year | Relevance | Discovered Via | Reasoning |")
        lines.append("|---|-------|---------|------|-----------|----------------|-----------|")
        for i, c in enumerate(maybe, 1):
            authors = c.get("authors", "[]")
            if isinstance(authors, str):
                try:
                    authors = ", ".join(json.loads(authors)[:2])
                except (json.JSONDecodeError, TypeError):
                    pass
            if len(authors) > 40:
                authors = authors[:37] + "..."
            title = c["title"]
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(
                f"| {i} | {title} | {authors} | {c.get('year', '?')} | "
                f"{c.get('relevance_score', '?')} | {c.get('discovered_via', '?')} | "
                f"{c.get('llm_reasoning', '')} |"
            )
        lines.append("")

    lines.append("## Strategy Breakdown")
    lines.append("")
    for strat, count in sorted(strat_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{strat}**: {count} candidates")
    lines.append("")

    content = "\n".join(lines)
    filepath.write_text(content, encoding="utf-8")
    logger.info(f"Report saved: {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Review CLI
# ---------------------------------------------------------------------------

def review_pending(conn):
    """Print pending candidates for review."""
    rows = conn.execute("""
        SELECT id, title, authors, year, relevance_score, novelty_score,
               llm_verdict, llm_reasoning, discovered_via, journal
        FROM discovery_queue
        WHERE status = 'pending_review'
        ORDER BY relevance_score DESC, novelty_score DESC
    """).fetchall()

    if not rows:
        print("No pending candidates.")
        return

    print(f"\n{'='*80}")
    print(f"PENDING REVIEW: {len(rows)} candidates")
    print(f"{'='*80}\n")

    for row in rows:
        authors = row["authors"] or "[]"
        try:
            authors = ", ".join(json.loads(authors)[:3])
        except (json.JSONDecodeError, TypeError):
            pass

        verdict_icon = {"accept": "+", "maybe": "?", "reject": "-"}.get(
            row["llm_verdict"], "?"
        )
        print(f"  [{verdict_icon}] ID {row['id']}: {row['title']}")
        print(f"      {authors} ({row['year'] or '?'}) — {row['journal'] or '?'}")
        print(f"      Relevance: {row['relevance_score']}/10  Novelty: {row['novelty_score']}/10")
        print(f"      Via: {row['discovered_via']}")
        print(f"      LLM: {row['llm_reasoning']}")
        print()


def accept_candidates(conn, ids):
    """Move candidates to accepted status."""
    now = datetime.now().isoformat()
    for cid in ids:
        conn.execute(
            "UPDATE discovery_queue SET status = 'accepted', reviewed_at = ? WHERE id = ?",
            (now, cid),
        )
    conn.commit()
    print(f"Accepted {len(ids)} candidate(s).")


def reject_candidates(conn, ids):
    """Move candidates to rejected status."""
    now = datetime.now().isoformat()
    for cid in ids:
        conn.execute(
            "UPDATE discovery_queue SET status = 'rejected', reviewed_at = ? WHERE id = ?",
            (now, cid),
        )
    conn.commit()
    print(f"Rejected {len(ids)} candidate(s).")


def show_stats(conn):
    """Print discovery statistics."""
    total = conn.execute("SELECT COUNT(*) FROM discovery_queue").fetchone()[0]
    if total == 0:
        print("No discovery candidates yet.")
        return

    print(f"\n{'='*60}")
    print("DISCOVERY STATISTICS")
    print(f"{'='*60}")
    print(f"Total candidates: {total}")

    for status in ("pending_review", "accepted", "rejected", "ingested", "deferred"):
        count = conn.execute(
            "SELECT COUNT(*) FROM discovery_queue WHERE status = ?", (status,)
        ).fetchone()[0]
        if count:
            print(f"  {status}: {count}")

    print("\nBy strategy:")
    rows = conn.execute("""
        SELECT
            CASE
                WHEN discovered_via LIKE 'refs_of:%' THEN 'refs'
                WHEN discovered_via LIKE 'cites:%' THEN 'cites'
                WHEN discovered_via LIKE 'author:%' THEN 'author_works'
                WHEN discovered_via LIKE 'web:%' THEN 'web'
                WHEN discovered_via LIKE 's2rec:%' THEN 's2_recommendations'
                ELSE 'other'
            END as strategy,
            COUNT(*) as cnt
        FROM discovery_queue
        GROUP BY strategy
        ORDER BY cnt DESC
    """).fetchall()
    for row in rows:
        print(f"  {row['strategy']}: {row['cnt']}")

    print("\nBy verdict:")
    rows = conn.execute("""
        SELECT llm_verdict, COUNT(*) as cnt
        FROM discovery_queue
        GROUP BY llm_verdict
        ORDER BY cnt DESC
    """).fetchall()
    for row in rows:
        print(f"  {row['llm_verdict'] or 'unscored'}: {row['cnt']}")

    avg = conn.execute(
        "SELECT AVG(relevance_score) FROM discovery_queue WHERE relevance_score IS NOT NULL"
    ).fetchone()[0]
    if avg:
        print(f"\nMean relevance score: {avg:.1f}")

    print()


# ---------------------------------------------------------------------------
# Main Discovery Run
# ---------------------------------------------------------------------------

STRATEGY_FUNCS = {
    "refs": discover_from_references,
    "cites": discover_from_citations,
    "author_works": discover_author_works,
    "web": discover_web_search,
    "s2_recommendations": discover_s2_recommendations,
}


def run_discovery(conn, strategies=None, limit=20, dry_run=False):
    """Run discovery strategies, score candidates, store results."""
    strategies = strategies or STRATEGIES
    all_candidates = []

    logger.info(f"Running discovery: strategies={strategies}, limit={limit}")

    for strat in strategies:
        func = STRATEGY_FUNCS.get(strat)
        if not func:
            logger.warning(f"Unknown strategy: {strat}")
            continue

        logger.info(f"\n--- Strategy: {strat} ---")
        try:
            candidates = func(conn, limit=limit)
            all_candidates.extend(candidates)
        except Exception as e:
            logger.error(f"Strategy {strat} failed: {e}")

    if not all_candidates:
        logger.info("No new candidates found.")
        return []

    # Score all candidates with LLM
    logger.info(f"\nScoring {len(all_candidates)} candidates via LLM...")
    try:
        backend = LLMBackend()
        for i, cand in enumerate(all_candidates):
            scores = score_candidate(backend, cand)
            cand.update(scores)
            if (i + 1) % 10 == 0:
                logger.info(f"  Scored {i + 1}/{len(all_candidates)}")
    except Exception as e:
        logger.error(f"LLM scoring setup failed: {e}")
        # Mark all as maybe so they still get stored
        for cand in all_candidates:
            if "llm_verdict" not in cand:
                cand["llm_verdict"] = "maybe"
                cand["llm_reasoning"] = f"Scoring unavailable: {e}"

    # Summary
    accepted = sum(1 for c in all_candidates if c.get("llm_verdict") == "accept")
    maybe = sum(1 for c in all_candidates if c.get("llm_verdict") == "maybe")
    rejected = sum(1 for c in all_candidates if c.get("llm_verdict") == "reject")

    logger.info(f"\nResults: {accepted} accept, {maybe} maybe, {rejected} reject")

    if dry_run:
        logger.info("[DRY RUN] Would store candidates — printing instead:")
        for cand in all_candidates:
            v = cand.get("llm_verdict", "?")
            r = cand.get("relevance_score", "?")
            print(f"  [{v}] (rel={r}) {cand['title'][:70]}")
        return all_candidates

    # Store
    stored = store_candidates(conn, all_candidates)
    logger.info(f"Stored {stored} candidates in discovery_queue")

    # Generate report
    generate_report(conn, all_candidates)

    # Print summary to stdout
    print(f"\n{'='*60}")
    print(f"DISCOVERY COMPLETE")
    print(f"{'='*60}")
    print(f"Candidates found: {len(all_candidates)}")
    print(f"  Accepted: {accepted}")
    print(f"  Maybe:    {maybe}")
    print(f"  Rejected: {rejected} (not stored)")
    print(f"Stored:     {stored}")
    print(f"{'='*60}")

    return all_candidates


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Literature discovery — snowball sampling from seed works/persons"
    )
    parser.add_argument(
        "--strategy", choices=STRATEGIES,
        help="Run only a specific strategy"
    )
    parser.add_argument("--review", action="store_true", help="Show pending candidates")
    parser.add_argument("--accept", type=int, nargs="+", metavar="ID", help="Accept candidates by ID")
    parser.add_argument("--reject", type=int, nargs="+", metavar="ID", help="Reject candidates by ID")
    parser.add_argument("--stats", action="store_true", help="Show discovery statistics")
    parser.add_argument("--dry-run", action="store_true", help="Preview without storing")
    parser.add_argument("--limit", type=int, default=20, help="Max candidates per strategy (default: 20)")

    args = parser.parse_args()

    conn = init_db()

    if args.review:
        review_pending(conn)
    elif args.accept:
        accept_candidates(conn, args.accept)
    elif args.reject:
        reject_candidates(conn, args.reject)
    elif args.stats:
        show_stats(conn)
    else:
        strategies = [args.strategy] if args.strategy else None
        run_discovery(conn, strategies=strategies, limit=args.limit, dry_run=args.dry_run)

    conn.close()


if __name__ == "__main__":
    main()
