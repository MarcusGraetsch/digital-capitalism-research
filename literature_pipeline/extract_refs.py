#!/usr/bin/env python3
"""Step 3: Extract bibliographic references from source texts.

Methods:
- GROBID (when available): State-of-the-art reference parser
- LLM fallback: Claude/OpenAI-based extraction
- Regex fallback: Basic pattern matching for common citation formats

Usage:
    python -m literature_pipeline.extract_refs [--source-id ID] [--method grobid|llm|regex]
"""

import argparse
import json
import re
from pathlib import Path

import requests as http_requests

from .db import (
    get_connection, init_db, get_sources_by_status, get_source_by_id,
    update_source, insert_reference,
)
from .llm_backend import LLMBackend
from .utils import setup_logging, logger, PIPELINE_DIR, load_config

EXTRACTED_DIR = PIPELINE_DIR / "extracted_text"


def _read_extracted_text(source):
    """Read the extracted markdown text for a source."""
    text_path = source["extracted_text_path"]
    if not text_path:
        return None
    full_path = PIPELINE_DIR / text_path
    if not full_path.exists():
        return None
    text = full_path.read_text(encoding="utf-8")
    # Strip YAML frontmatter
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    return text.strip()


# ---------------------------------------------------------------------------
# GROBID extraction
# ---------------------------------------------------------------------------

def extract_refs_grobid(source_path, grobid_url="http://localhost:8070"):
    """Extract references using GROBID service."""
    endpoint = f"{grobid_url}/api/processReferences"
    try:
        with open(source_path, "rb") as f:
            resp = http_requests.post(
                endpoint,
                files={"input": f},
                timeout=120,
            )
        if resp.status_code != 200:
            logger.warning(f"GROBID returned {resp.status_code}")
            return None

        # Parse TEI XML response
        from xml.etree import ElementTree as ET
        ns = {"tei": "http://www.tei-c.org/ns/1.0"}
        root = ET.fromstring(resp.text)

        refs = []
        for bibl in root.findall(".//tei:biblStruct", ns):
            ref = {}
            # Title
            title_el = bibl.find(".//tei:title[@level='a']", ns) or bibl.find(".//tei:title[@level='m']", ns)
            if title_el is not None and title_el.text:
                ref["parsed_title"] = title_el.text.strip()

            # Authors
            authors = []
            for author in bibl.findall(".//tei:author/tei:persName", ns):
                first = author.findtext("tei:forename", "", ns).strip()
                last = author.findtext("tei:surname", "", ns).strip()
                if last:
                    authors.append(f"{last}, {first}".strip(", "))
            ref["parsed_authors"] = authors

            # Year
            date_el = bibl.find(".//tei:date[@type='published']", ns)
            if date_el is not None:
                year_str = date_el.get("when", "")[:4]
                if year_str.isdigit():
                    ref["parsed_year"] = int(year_str)

            # DOI
            doi_el = bibl.find(".//tei:idno[@type='DOI']", ns)
            if doi_el is not None and doi_el.text:
                ref["parsed_doi"] = doi_el.text.strip()

            # Journal
            journal_el = bibl.find(".//tei:title[@level='j']", ns)
            if journal_el is not None and journal_el.text:
                ref["parsed_journal"] = journal_el.text.strip()

            # Raw text representation
            parts = []
            if ref.get("parsed_authors"):
                parts.append("; ".join(ref["parsed_authors"]))
            if ref.get("parsed_year"):
                parts.append(f"({ref['parsed_year']})")
            if ref.get("parsed_title"):
                parts.append(ref["parsed_title"])
            ref["raw_text"] = " ".join(parts) if parts else str(bibl.text or "")

            if ref.get("parsed_title") or ref.get("parsed_authors"):
                refs.append(ref)

        return refs

    except http_requests.ConnectionError:
        logger.info("GROBID not available (connection refused)")
        return None
    except Exception as e:
        logger.warning(f"GROBID extraction failed: {e}")
        return None


def _is_grobid_available(url):
    """Check if GROBID service is running."""
    try:
        resp = http_requests.get(f"{url}/api/isalive", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# LLM extraction
# ---------------------------------------------------------------------------

REFS_EXTRACTION_PROMPT = """Analyze the following academic text and extract ALL bibliographic references cited in it.

For each reference, provide:
- raw_text: The full reference as it appears
- parsed_authors: List of author names (Last, First format)
- parsed_title: Title of the work
- parsed_year: Publication year (integer)
- parsed_doi: DOI if mentioned
- parsed_journal: Journal name if applicable

Return a JSON array of objects. Only include references you are confident about.
If the text has no clear references section, extract in-text citations (Author, Year) format.

TEXT:
{text}"""


def extract_refs_llm(text, llm):
    """Extract references using LLM."""
    # Truncate to avoid token limits - focus on bibliography section
    # Try to find the references/bibliography section
    ref_section = None
    for marker in ["References", "Bibliography", "Literatur", "Works Cited",
                    "Quellenverzeichnis", "Literaturverzeichnis"]:
        idx = text.lower().rfind(marker.lower())
        if idx != -1:
            ref_section = text[idx:]
            break

    if ref_section and len(ref_section) > 500:
        text_to_send = ref_section[:15000]
    else:
        # Send last portion of text (likely to contain references)
        text_to_send = text[-15000:]

    prompt = REFS_EXTRACTION_PROMPT.format(text=text_to_send)
    try:
        refs = llm.complete_json(prompt, task="extract_refs")
        if isinstance(refs, dict) and "references" in refs:
            refs = refs["references"]
        if not isinstance(refs, list):
            return []
        return refs
    except Exception as e:
        logger.warning(f"LLM ref extraction failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Regex extraction (basic fallback)
# ---------------------------------------------------------------------------

def extract_refs_regex(text):
    """Basic regex extraction for common citation patterns."""
    refs = []

    # Pattern: Author (Year) or (Author, Year) in-text citations
    inline_pattern = re.compile(
        r"(?:([A-Z][a-z]+(?:\s+(?:and|&|und)\s+[A-Z][a-z]+)?)\s*\((\d{4})\))"
        r"|(?:\(([A-Z][a-z]+(?:\s+(?:and|&|und)\s+[A-Z][a-z]+)?),?\s*(\d{4})\))"
    )

    seen = set()
    for match in inline_pattern.finditer(text):
        author = match.group(1) or match.group(3)
        year = match.group(2) or match.group(4)
        key = f"{author}_{year}"
        if key not in seen:
            seen.add(key)
            refs.append({
                "raw_text": f"{author} ({year})",
                "parsed_authors": [author],
                "parsed_year": int(year),
            })

    return refs


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_source(conn, source, method=None, llm=None):
    """Extract references for a single source."""
    logger.info(f"[{source['id']}] Extracting refs: {source['title'][:60]}...")

    config = load_config()
    grobid_cfg = config.get("extraction", {}).get("grobid", {})
    grobid_url = grobid_cfg.get("url", "http://localhost:8070")

    refs = None
    method_used = method

    # Try GROBID first if we have the original PDF
    if (not method or method == "grobid") and source["source_path"]:
        source_path = Path(source["source_path"])
        if source_path.exists() and source_path.suffix.lower() == ".pdf":
            if _is_grobid_available(grobid_url):
                refs = extract_refs_grobid(str(source_path), grobid_url)
                if refs:
                    method_used = "grobid"

    # LLM fallback
    if not refs and (not method or method == "llm"):
        text = _read_extracted_text(source)
        if text:
            if not llm:
                llm = LLMBackend()
            refs = extract_refs_llm(text, llm)
            if refs:
                method_used = "llm"

    # Regex fallback
    if not refs and (not method or method == "regex"):
        text = _read_extracted_text(source)
        if text:
            refs = extract_refs_regex(text)
            if refs:
                method_used = "regex"

    if not refs:
        logger.info(f"[{source['id']}] No references found")
        update_source(conn, source["id"], status="refs_extracted")
        return 0

    # Insert references into DB
    count = 0
    for ref in refs:
        authors = ref.get("parsed_authors", [])
        if isinstance(authors, str):
            authors = [authors]
        insert_reference(
            conn,
            source_id=source["id"],
            raw_text=ref.get("raw_text", ""),
            parsed_authors=authors,
            parsed_title=ref.get("parsed_title"),
            parsed_year=ref.get("parsed_year"),
            parsed_doi=ref.get("parsed_doi"),
            parsed_journal=ref.get("parsed_journal"),
            extraction_method=method_used,
            confidence=ref.get("confidence", 0.7 if method_used == "grobid" else 0.5),
        )
        count += 1

    update_source(conn, source["id"], status="refs_extracted")
    logger.info(f"[{source['id']}] Extracted {count} references via {method_used}")
    return count


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Extract references from source texts")
    parser.add_argument("--source-id", type=int, help="Process a specific source")
    parser.add_argument("--method", choices=["grobid", "llm", "regex"], help="Force method")
    parser.add_argument("--limit", type=int, help="Max sources to process")
    args = parser.parse_args()

    conn = init_db()
    llm = None

    if args.source_id:
        source = get_source_by_id(conn, args.source_id)
        if not source:
            logger.error(f"Source {args.source_id} not found")
            return
        process_source(conn, source, args.method)
    else:
        sources = get_sources_by_status(conn, "text_extracted")
        if not sources:
            logger.info("No sources pending reference extraction")
            return

        if args.limit:
            sources = sources[:args.limit]

        logger.info(f"Processing {len(sources)} sources...")
        total_refs = 0
        for source in sources:
            total_refs += process_source(conn, source, args.method, llm)
        logger.info(f"Reference extraction complete: {total_refs} total references")

    conn.close()


if __name__ == "__main__":
    main()
