#!/usr/bin/env python3
"""Step 5: Build citation graph from extracted references.

Resolves extracted_references to known sources in the DB,
creates citation edges, and exports graph in JSON and DOT formats.

Usage:
    python -m literature_pipeline.build_graph                    # Resolve refs + export
    python -m literature_pipeline.build_graph --export-only      # Just export existing graph
    python -m literature_pipeline.build_graph --format json      # Export JSON only
    python -m literature_pipeline.build_graph --format dot       # Export DOT only
"""

import argparse
import json
import re
from pathlib import Path

from .db import (
    get_connection, init_db, insert_citation,
)
from .utils import setup_logging, logger, PIPELINE_DIR


GRAPH_DIR = PIPELINE_DIR / "knowledge"


def _normalize_name(name):
    """Normalize author name for fuzzy matching."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    # Handle "Last, First" → "last first"
    name = re.sub(r"\s+", " ", name)
    return name


def _title_similarity(a, b):
    """Simple word-overlap similarity between two titles."""
    if not a or not b:
        return 0.0
    words_a = set(re.findall(r"\w{3,}", a.lower()))
    words_b = set(re.findall(r"\w{3,}", b.lower()))
    if not words_a or not words_b:
        return 0.0
    overlap = words_a & words_b
    return len(overlap) / min(len(words_a), len(words_b))


def _author_match(ref_authors, source_authors):
    """Check if any reference author matches any source author."""
    if not ref_authors or not source_authors:
        return False
    ref_normalized = {_normalize_name(a) for a in ref_authors}
    src_normalized = {_normalize_name(a) for a in source_authors}

    for ra in ref_normalized:
        ra_parts = ra.split()
        for sa in src_normalized:
            sa_parts = sa.split()
            # Match on last name
            if ra_parts and sa_parts and ra_parts[0] == sa_parts[0]:
                return True
    return False


def resolve_references(conn):
    """Try to match extracted_references to known sources in the DB."""
    # Load all sources for matching
    sources = conn.execute("SELECT * FROM sources").fetchall()
    source_map = {s["id"]: s for s in sources}

    # Load all unresolved references
    refs = conn.execute(
        "SELECT * FROM extracted_references WHERE resolved_source_id IS NULL"
    ).fetchall()

    if not refs:
        logger.info("No unresolved references to process")
        return 0

    logger.info(f"Resolving {len(refs)} references against {len(sources)} sources...")
    resolved = 0

    for ref in refs:
        ref_authors_raw = ref["parsed_authors"]
        if isinstance(ref_authors_raw, str):
            try:
                ref_authors = json.loads(ref_authors_raw)
            except (json.JSONDecodeError, TypeError):
                ref_authors = [ref_authors_raw] if ref_authors_raw else []
        else:
            ref_authors = ref_authors_raw or []

        ref_title = ref["parsed_title"] or ""
        ref_year = ref["parsed_year"]
        best_match = None
        best_score = 0.0

        for source in sources:
            # Don't match a source to its own references
            if source["id"] == ref["source_id"]:
                continue

            src_authors_raw = source["authors"]
            if isinstance(src_authors_raw, str):
                try:
                    src_authors = json.loads(src_authors_raw)
                except (json.JSONDecodeError, TypeError):
                    src_authors = [src_authors_raw] if src_authors_raw else []
            else:
                src_authors = src_authors_raw or []

            score = 0.0

            # Author match
            if _author_match(ref_authors, src_authors):
                score += 0.4

            # Year match
            if ref_year and source["year"] and ref_year == source["year"]:
                score += 0.2

            # Title similarity
            title_sim = _title_similarity(ref_title, source["title"])
            score += title_sim * 0.4

            # DOI exact match (strong signal)
            if ref["parsed_doi"] and source.get("doi"):
                if ref["parsed_doi"].lower() == source["doi"].lower():
                    score = 1.0

            if score > best_score and score >= 0.5:
                best_score = score
                best_match = source

        if best_match:
            conn.execute(
                "UPDATE extracted_references SET resolved_source_id = ? WHERE id = ?",
                (best_match["id"], ref["id"]),
            )

            # Create citation edge
            insert_citation(
                conn,
                citing_id=ref["source_id"],
                cited_id=best_match["id"],
                context=ref["raw_text"],
                citation_type="mentions",
            )
            resolved += 1

    conn.commit()
    logger.info(f"Resolved {resolved}/{len(refs)} references")
    return resolved


def _classify_citation_type(conn):
    """Use knowledge_items (critiques) to upgrade citation types."""
    # Find critiques that name specific authors/works
    critiques = conn.execute(
        "SELECT * FROM knowledge_items WHERE item_type = 'critique' AND target_author IS NOT NULL"
    ).fetchall()

    updated = 0
    for critique in critiques:
        # Try to find a matching citation edge
        rows = conn.execute(
            """SELECT c.id, s.authors FROM citations c
               JOIN sources s ON s.id = c.cited_source_id
               WHERE c.citing_source_id = ?""",
            (critique["source_id"],),
        ).fetchall()

        target = _normalize_name(critique["target_author"])
        for row in rows:
            src_authors_raw = row["authors"]
            if isinstance(src_authors_raw, str):
                try:
                    src_authors = json.loads(src_authors_raw)
                except (json.JSONDecodeError, TypeError):
                    src_authors = [src_authors_raw]
            else:
                src_authors = src_authors_raw or []

            for sa in src_authors:
                if target in _normalize_name(sa):
                    conn.execute(
                        "UPDATE citations SET citation_type = 'critiques' WHERE id = ?",
                        (row["id"],),
                    )
                    updated += 1
                    break

    conn.commit()
    if updated:
        logger.info(f"Classified {updated} citations as critiques")


def export_json(conn):
    """Export citation graph as JSON."""
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    sources = conn.execute("SELECT id, title, authors, year, type FROM sources").fetchall()
    citations = conn.execute(
        "SELECT citing_source_id, cited_source_id, citation_type, context FROM citations"
    ).fetchall()

    nodes = []
    for s in sources:
        authors = s["authors"]
        if isinstance(authors, str):
            try:
                authors = json.loads(authors)
            except (json.JSONDecodeError, TypeError):
                authors = [authors] if authors else []
        nodes.append({
            "id": s["id"],
            "title": s["title"],
            "authors": authors,
            "year": s["year"],
            "type": s["type"],
        })

    edges = []
    for c in citations:
        edges.append({
            "source": c["citing_source_id"],
            "target": c["cited_source_id"],
            "type": c["citation_type"],
            "context": c["context"],
        })

    graph = {"nodes": nodes, "edges": edges}
    out_path = GRAPH_DIR / "citation_graph.json"
    out_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Exported JSON graph: {len(nodes)} nodes, {len(edges)} edges -> {out_path}")
    return out_path


def export_dot(conn):
    """Export citation graph as Graphviz DOT format."""
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    sources = conn.execute("SELECT id, title, authors, year FROM sources").fetchall()
    citations = conn.execute(
        "SELECT citing_source_id, cited_source_id, citation_type FROM citations"
    ).fetchall()

    # Only include sources that appear in citations
    cited_ids = set()
    for c in citations:
        cited_ids.add(c["citing_source_id"])
        cited_ids.add(c["cited_source_id"])

    lines = ['digraph citations {', '  rankdir=LR;', '  node [shape=box, style=rounded];', '']

    for s in sources:
        if s["id"] not in cited_ids:
            continue
        authors = s["authors"]
        if isinstance(authors, str):
            try:
                authors = json.loads(authors)
            except (json.JSONDecodeError, TypeError):
                authors = [authors] if authors else []
        first_author = authors[0].split(",")[0].strip() if authors else "?"
        label = f"{first_author} ({s['year'] or '?'})"
        label = label.replace('"', '\\"')
        lines.append(f'  n{s["id"]} [label="{label}"];')

    lines.append('')

    type_styles = {
        "supports": "color=green",
        "critiques": "color=red",
        "extends": "color=blue",
        "mentions": "color=gray",
    }

    for c in citations:
        style = type_styles.get(c["citation_type"], "")
        lines.append(f'  n{c["citing_source_id"]} -> n{c["cited_source_id"]} [{style}];')

    lines.append('}')

    out_path = GRAPH_DIR / "citation_graph.dot"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Exported DOT graph -> {out_path}")
    return out_path


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Build and export citation graph")
    parser.add_argument("--export-only", action="store_true", help="Skip resolution, just export")
    parser.add_argument("--format", choices=["json", "dot", "both"], default="both")
    args = parser.parse_args()

    conn = init_db()

    if not args.export_only:
        resolve_references(conn)
        _classify_citation_type(conn)

    if args.format in ("json", "both"):
        export_json(conn)
    if args.format in ("dot", "both"):
        export_dot(conn)

    # Print summary
    total_citations = conn.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    logger.info(f"Total citation edges: {total_citations}")

    conn.close()


if __name__ == "__main__":
    main()
