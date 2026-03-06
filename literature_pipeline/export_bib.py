#!/usr/bin/env python3
"""Step 6: Bidirectional sync between literature.db and bibliography.bib.

- Reads existing .bib entries and avoids duplicating them
- Appends new sources (from DB) to a PIPELINE-ADDED section
- Never modifies existing entries
- Can also import .bib entries into the DB (--import mode)

Usage:
    python -m literature_pipeline.export_bib                 # Export new DB entries to .bib
    python -m literature_pipeline.export_bib --import        # Import .bib entries into DB
    python -m literature_pipeline.export_bib --dry-run       # Preview without writing
"""

import argparse
import json
import re
from pathlib import Path

from .db import get_connection, init_db, get_source_by_bibtex_key
from .ingest import ingest_from_bibtex
from .utils import setup_logging, logger, repo_root, sanitize_filename


PIPELINE_MARKER = "% PIPELINE-ADDED ENTRIES"


def _get_bib_path():
    """Return path to bibliography.bib."""
    return repo_root() / "literature" / "bibliography.bib"


def _existing_bibtex_keys(bib_path):
    """Extract all existing BibTeX keys from a .bib file."""
    text = bib_path.read_text(encoding="utf-8")
    return set(re.findall(r"@\w+\{([^,]+),", text))


def _source_type_to_bibtex(source_type):
    """Map our source types to BibTeX entry types."""
    mapping = {
        "book": "book",
        "paper": "article",
        "chapter": "incollection",
        "article": "article",
        "report": "techreport",
        "thesis": "phdthesis",
    }
    return mapping.get(source_type, "misc")


def _generate_bibtex_key(source):
    """Generate a BibTeX key from source metadata."""
    authors = source["authors"]
    if isinstance(authors, str):
        try:
            authors = json.loads(authors)
        except (json.JSONDecodeError, TypeError):
            authors = [authors] if authors else []

    if authors:
        first_author = authors[0].split(",")[0].strip().lower()
        first_author = re.sub(r"[^\w]", "", first_author)
    else:
        first_author = "unknown"

    # Short title word
    title_word = ""
    if source["title"]:
        words = source["title"].lower().split()
        skip = {"the", "a", "an", "of", "in", "on", "and", "for", "to", "der", "die", "das", "und", "zur"}
        for w in words:
            clean = re.sub(r"[^\w]", "", w)
            if clean and clean not in skip:
                title_word = clean
                break

    year = source["year"] or "nd"
    return f"{first_author}_{title_word}_{year}"


def _format_bibtex_entry(source):
    """Format a source as a BibTeX entry string."""
    key = source["bibtex_key"] or _generate_bibtex_key(source)
    entry_type = _source_type_to_bibtex(source["type"] or "book")

    authors = source["authors"]
    if isinstance(authors, str):
        try:
            authors = json.loads(authors)
        except (json.JSONDecodeError, TypeError):
            authors = [authors] if authors else []

    fields = []
    if authors:
        fields.append(f"  author      = {{{' and '.join(authors)}}}")
    fields.append(f"  title       = {{{source['title']}}}")
    if source["year"]:
        fields.append(f"  year        = {{{source['year']}}}")
    if source.get("publisher"):
        fields.append(f"  publisher   = {{{source['publisher']}}}")
    if source.get("journal"):
        fields.append(f"  journal     = {{{source['journal']}}}")
    if source.get("doi"):
        fields.append(f"  doi         = {{{source['doi']}}}")
    if source.get("isbn"):
        fields.append(f"  isbn        = {{{source['isbn']}}}")

    tags = source.get("tags")
    if tags:
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except (json.JSONDecodeError, TypeError):
                tags = []
        if tags:
            fields.append(f"  keywords    = {{{', '.join(tags)}}}")

    if source.get("notes"):
        fields.append(f"  note        = {{{source['notes']}}}")

    body = ",\n".join(fields)
    return f"@{entry_type}{{{key},\n{body}\n}}", key


def export_to_bib(conn, dry_run=False):
    """Export new sources from DB to bibliography.bib."""
    bib_path = _get_bib_path()
    if not bib_path.exists():
        logger.error(f"Bibliography not found: {bib_path}")
        return

    existing_keys = _existing_bibtex_keys(bib_path)
    logger.info(f"Existing .bib entries: {len(existing_keys)}")

    # Get all sources that have a bibtex_key or can generate one
    cursor = conn.execute("SELECT * FROM sources ORDER BY year, id")
    sources = cursor.fetchall()

    new_entries = []
    for source in sources:
        key = source["bibtex_key"]
        if key and key in existing_keys:
            continue  # Already in .bib

        entry_text, generated_key = _format_bibtex_entry(source)

        if generated_key in existing_keys:
            continue  # Key collision with existing

        new_entries.append((source, entry_text, generated_key))

    if not new_entries:
        logger.info("No new entries to export")
        return

    logger.info(f"New entries to add: {len(new_entries)}")

    if dry_run:
        for source, entry_text, key in new_entries:
            print(f"\n{entry_text}")
        return

    # Read current .bib content
    bib_text = bib_path.read_text(encoding="utf-8")

    # Find or create the pipeline section
    if PIPELINE_MARKER not in bib_text:
        # Insert before the COMMENTS section, or at end
        comments_idx = bib_text.find("% COMMENTS AND NOTES")
        if comments_idx != -1:
            insert_point = comments_idx
        else:
            insert_point = len(bib_text)

        section_header = f"""
% =============================================================================
{PIPELINE_MARKER}
% Added automatically by literature_pipeline/export_bib.py
% =============================================================================

"""
        bib_text = bib_text[:insert_point] + section_header + bib_text[insert_point:]

    # Append new entries after the marker
    marker_idx = bib_text.find(PIPELINE_MARKER)
    # Find end of the marker line block (next blank line after section header)
    insert_after = bib_text.find("\n\n", marker_idx + len(PIPELINE_MARKER))
    if insert_after == -1:
        insert_after = len(bib_text)
    else:
        insert_after += 2  # Past the double newline

    entries_text = ""
    for source, entry_text, key in new_entries:
        entries_text += entry_text + "\n\n"

        # Update the source's bibtex_key in DB if it didn't have one
        if not source["bibtex_key"]:
            conn.execute(
                "UPDATE sources SET bibtex_key = ? WHERE id = ?",
                (key, source["id"]),
            )

    conn.commit()
    bib_text = bib_text[:insert_after] + entries_text + bib_text[insert_after:]

    bib_path.write_text(bib_text, encoding="utf-8")
    logger.info(f"Appended {len(new_entries)} entries to {bib_path}")


def import_from_bib(conn):
    """Import .bib entries into the database (wrapper around ingest)."""
    bib_path = _get_bib_path()
    if not bib_path.exists():
        logger.error(f"Bibliography not found: {bib_path}")
        return
    imported, skipped = ingest_from_bibtex(conn, str(bib_path))
    logger.info(f"Import complete: {imported} new, {skipped} already existed")


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Sync bibliography.bib with literature DB")
    parser.add_argument("--import", dest="import_mode", action="store_true",
                        help="Import .bib entries into DB")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    conn = init_db()

    if args.import_mode:
        import_from_bib(conn)
    else:
        export_to_bib(conn, dry_run=args.dry_run)

    conn.close()


if __name__ == "__main__":
    main()
