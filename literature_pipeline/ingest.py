#!/usr/bin/env python3
"""Step 1: Register source metadata in the literature database.

Usage:
    python -m literature_pipeline.ingest --file path/to.pdf --title "Title" --authors "Author" --year 2024
    python -m literature_pipeline.ingest --from-bibtex ../literature/bibliography.bib [--source-dir /path/to/pdfs]
    python -m literature_pipeline.ingest --from-csv sources.csv
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from .db import get_connection, init_db, insert_source, get_source_by_bibtex_key, stats
from .utils import setup_logging, logger, source_library


# ---------------------------------------------------------------------------
# BibTeX parser (lightweight, no external dependency)
# ---------------------------------------------------------------------------

def parse_bibtex(bib_path):
    """Parse a .bib file into a list of entry dicts.

    Handles the format used in bibliography.bib:
    @type{key, field = {value}, ...}
    """
    text = Path(bib_path).read_text(encoding="utf-8")
    entries = []

    # Match each @type{key, ...} block
    pattern = re.compile(
        r"@(\w+)\s*\{\s*([^,]+)\s*,\s*(.*?)\n\s*\}",
        re.DOTALL,
    )

    for match in pattern.finditer(text):
        entry_type = match.group(1).lower()
        bibtex_key = match.group(2).strip()
        body = match.group(3)

        entry = {"type": entry_type, "bibtex_key": bibtex_key}

        # Parse field = {value} or field = "value"
        field_pattern = re.compile(
            r"(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|\"([^\"]*)\"|\s*(\d+)\s*)",
        )
        for fmatch in field_pattern.finditer(body):
            field_name = fmatch.group(1).lower()
            value = fmatch.group(2) or fmatch.group(3) or fmatch.group(4) or ""
            entry[field_name] = value.strip()

        entries.append(entry)

    return entries


def _bibtex_type_to_source_type(bib_type):
    """Map BibTeX entry types to our source types."""
    mapping = {
        "book": "book",
        "article": "paper",
        "inproceedings": "paper",
        "incollection": "chapter",
        "phdthesis": "thesis",
        "mastersthesis": "thesis",
        "techreport": "report",
        "misc": "article",
        "online": "article",
    }
    return mapping.get(bib_type, "paper")


def _parse_authors_string(authors_str):
    """Parse 'Last, First and Last2, First2' into a list."""
    if not authors_str:
        return []
    parts = re.split(r"\s+and\s+", authors_str)
    return [a.strip() for a in parts if a.strip()]


def _find_source_file(bibtex_key, authors, year, source_dir):
    """Try to find a matching PDF/ePub in the source directory.

    Searches for files matching patterns like:
    - {bibtex_key}.pdf
    - {author}_{year}*.pdf
    - {author} - {title}*.pdf
    """
    if not source_dir or not Path(source_dir).exists():
        return None

    source_dir = Path(source_dir)

    # Direct key match
    for ext in (".pdf", ".epub", ".djvu"):
        candidate = source_dir / f"{bibtex_key}{ext}"
        if candidate.exists():
            return str(candidate)

    # Author+year pattern
    if authors and year:
        first_author = authors[0].split(",")[0].strip().lower()
        for f in source_dir.iterdir():
            fname = f.name.lower()
            if first_author in fname and str(year) in fname:
                if f.suffix.lower() in (".pdf", ".epub", ".djvu"):
                    return str(f)

    return None


# ---------------------------------------------------------------------------
# Ingest functions
# ---------------------------------------------------------------------------

def ingest_single(conn, title, authors, year, file_path=None, type_="book",
                  format_=None, bibtex_key=None, **extra):
    """Ingest a single source."""
    # Detect format from file extension
    if file_path and not format_:
        ext = Path(file_path).suffix.lower()
        format_ = {"pdf": "pdf", ".epub": "epub", ".djvu": "scan", ".html": "html"}.get(ext, "pdf")
    format_ = format_ or "pdf"

    # Check for duplicate bibtex_key
    if bibtex_key and get_source_by_bibtex_key(conn, bibtex_key):
        logger.info(f"  Skipped (exists): {bibtex_key}")
        return None

    authors_list = authors if isinstance(authors, list) else _parse_authors_string(authors)

    source_id = insert_source(
        conn,
        title=title,
        authors=authors_list,
        year=int(year) if year else None,
        type=type_,
        format=format_,
        bibtex_key=bibtex_key,
        source_path=str(file_path) if file_path else None,
        **extra,
    )
    logger.info(f"  Ingested [{source_id}]: {title[:60]}")
    return source_id


def ingest_from_bibtex(conn, bib_path, source_dir=None):
    """Bulk-ingest from a .bib file."""
    entries = parse_bibtex(bib_path)
    logger.info(f"Parsed {len(entries)} entries from {bib_path}")

    imported = 0
    skipped = 0

    for entry in entries:
        bibtex_key = entry.get("bibtex_key")
        if not bibtex_key:
            continue

        if get_source_by_bibtex_key(conn, bibtex_key):
            skipped += 1
            continue

        authors = _parse_authors_string(entry.get("author", ""))
        year = entry.get("year")
        title = entry.get("title", bibtex_key)
        source_type = _bibtex_type_to_source_type(entry.get("type", "misc"))

        # Try to find the actual file
        source_path = _find_source_file(bibtex_key, authors, year, source_dir)

        extra = {}
        if entry.get("publisher"):
            extra["publisher"] = entry["publisher"]
        if entry.get("journal"):
            extra["journal"] = entry["journal"]
        if entry.get("doi"):
            extra["doi"] = entry["doi"]
        if entry.get("isbn"):
            extra["isbn"] = entry["isbn"]
        if entry.get("note"):
            extra["notes"] = entry["note"]
        if entry.get("keywords"):
            extra["tags"] = [k.strip() for k in entry["keywords"].split(",")]
        if entry.get("language"):
            extra["language"] = entry["language"]

        sid = ingest_single(
            conn,
            title=title,
            authors=authors,
            year=year,
            file_path=source_path,
            type_=source_type,
            bibtex_key=bibtex_key,
            **extra,
        )
        if sid:
            imported += 1

    logger.info(f"BibTeX import: {imported} imported, {skipped} skipped (already exist)")
    return imported, skipped


def ingest_from_csv(conn, csv_path, source_dir=None):
    """Bulk-ingest from a CSV file.

    Expected columns: title, authors, year, type, bibtex_key, file_path
    Optional: publisher, journal, doi, tags, language, priority
    """
    imported = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_path = row.get("file_path")
            if file_path and source_dir and not Path(file_path).is_absolute():
                file_path = str(Path(source_dir) / file_path)

            extra = {}
            for field in ("publisher", "journal", "doi", "isbn", "language", "notes"):
                if row.get(field):
                    extra[field] = row[field]
            if row.get("tags"):
                extra["tags"] = [t.strip() for t in row["tags"].split(";")]
            if row.get("priority"):
                extra["priority"] = int(row["priority"])

            sid = ingest_single(
                conn,
                title=row["title"],
                authors=row.get("authors", ""),
                year=row.get("year"),
                file_path=file_path,
                type_=row.get("type", "book"),
                bibtex_key=row.get("bibtex_key"),
                **extra,
            )
            if sid:
                imported += 1

    logger.info(f"CSV import: {imported} imported")
    return imported


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Ingest literature sources")
    parser.add_argument("--file", help="Path to a single source file")
    parser.add_argument("--title", help="Title of the source")
    parser.add_argument("--authors", help="Authors (comma or 'and' separated)")
    parser.add_argument("--year", type=int, help="Publication year")
    parser.add_argument("--type", default="book", help="Source type: book, paper, chapter, etc.")
    parser.add_argument("--bibtex-key", help="BibTeX citation key")
    parser.add_argument("--from-bibtex", help="Bulk import from .bib file")
    parser.add_argument("--from-csv", help="Bulk import from .csv file")
    parser.add_argument("--source-dir", help="Directory to search for source files")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")

    args = parser.parse_args()
    conn = init_db()

    if args.stats:
        s = stats(conn)
        for k, v in s.items():
            print(f"  {k}: {v}")
        conn.close()
        return

    if args.from_bibtex:
        ingest_from_bibtex(conn, args.from_bibtex, args.source_dir)
    elif args.from_csv:
        ingest_from_csv(conn, args.from_csv, args.source_dir)
    elif args.title:
        ingest_single(
            conn,
            title=args.title,
            authors=args.authors or "",
            year=args.year,
            file_path=args.file,
            type_=args.type,
            bibtex_key=args.bibtex_key,
        )
    else:
        parser.print_help()
        sys.exit(1)

    s = stats(conn)
    logger.info(f"Database now has {s['total_sources']} sources")
    conn.close()


if __name__ == "__main__":
    main()
