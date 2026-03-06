#!/usr/bin/env python3
"""Step 2: Extract text from PDFs, scans, and ePubs.

Methods (tried in order based on format):
- PyMuPDF (pymupdf): Fast, for digital PDFs
- Tesseract (pytesseract): For scanned documents / OCR
- ebooklib: For ePub files

Output: extracted_text/{source_id}.md with YAML frontmatter.

Usage:
    python -m literature_pipeline.extract_text [--source-id ID] [--method pymupdf|tesseract]
"""

import argparse
import re
import subprocess
from pathlib import Path

from .db import get_connection, init_db, get_sources_by_status, get_source_by_id, update_source
from .utils import setup_logging, logger, PIPELINE_DIR, load_config

EXTRACTED_DIR = PIPELINE_DIR / "extracted_text"


def extract_pymupdf(pdf_path):
    """Extract text using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("pip install PyMuPDF")

    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"<!-- Page {i + 1} -->\n\n{text.strip()}")
    doc.close()

    if not pages:
        return None
    return "\n\n---\n\n".join(pages)


def extract_tesseract(pdf_path, lang="deu+eng"):
    """Extract text from scanned PDF using Tesseract OCR."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        raise ImportError("pip install pdf2image pytesseract")

    images = convert_from_path(pdf_path)
    pages = []
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img, lang=lang)
        if text.strip():
            pages.append(f"<!-- Page {i + 1} -->\n\n{text.strip()}")

    if not pages:
        return None
    return "\n\n---\n\n".join(pages)


def extract_epub(epub_path):
    """Extract text from ePub file."""
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("pip install EbookLib beautifulsoup4")

    book = epub.read_epub(epub_path)
    chapters = []

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        if text.strip() and len(text.strip()) > 50:
            chapters.append(text.strip())

    if not chapters:
        return None
    return "\n\n---\n\n".join(chapters)


def _is_scanned_pdf(pdf_path):
    """Heuristic: a PDF is 'scanned' if PyMuPDF extracts very little text."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        total_chars = 0
        total_pages = len(doc)
        for page in doc:
            total_chars += len(page.get_text("text").strip())
        doc.close()
        if total_pages == 0:
            return True
        chars_per_page = total_chars / total_pages
        return chars_per_page < 100  # Likely scanned if < 100 chars/page
    except Exception:
        return True


def extract_text_for_source(conn, source, method=None):
    """Extract text for a single source. Returns (text, method_used)."""
    source_path = source["source_path"]
    if not source_path or not Path(source_path).exists():
        logger.warning(f"  Source file not found: {source_path}")
        return None, None

    path = Path(source_path)
    ext = path.suffix.lower()
    config = load_config()
    ocr_lang = config.get("extraction", {}).get("tesseract", {}).get("lang", "deu+eng")

    if ext == ".epub":
        text = extract_epub(path)
        return text, "epub"

    if ext in (".pdf", ".djvu"):
        if method == "tesseract":
            text = extract_tesseract(path, lang=ocr_lang)
            return text, "tesseract"
        if method == "pymupdf" or not method:
            # Try PyMuPDF first
            if not _is_scanned_pdf(path):
                text = extract_pymupdf(path)
                if text:
                    return text, "pymupdf"
            # Fall back to Tesseract for scans
            logger.info(f"  Scanned PDF detected, using Tesseract OCR...")
            try:
                text = extract_tesseract(path, lang=ocr_lang)
                return text, "tesseract"
            except ImportError:
                logger.warning("  Tesseract not available, skipping OCR")
                return None, None

    logger.warning(f"  Unsupported format: {ext}")
    return None, None


def save_extracted_text(source, text, method):
    """Save extracted text as markdown with frontmatter."""
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    import json
    authors = source["authors"]
    if isinstance(authors, str):
        try:
            authors = json.loads(authors)
        except (json.JSONDecodeError, TypeError):
            authors = [authors] if authors else []

    authors_str = ", ".join(authors) if authors else "Unknown"

    out_path = EXTRACTED_DIR / f"{source['id']}.md"
    content = f"""---
source_id: {source['id']}
title: "{source['title']}"
authors: "{authors_str}"
year: {source['year'] or 'unknown'}
extraction_method: {method}
---

# {source['title']}

**Authors:** {authors_str}
**Year:** {source['year'] or 'unknown'}
**Extraction:** {method}

---

{text}
"""
    out_path.write_text(content, encoding="utf-8")
    return str(out_path.relative_to(PIPELINE_DIR))


def process_source(conn, source, method=None):
    """Extract text for one source and update the DB."""
    logger.info(f"[{source['id']}] Extracting: {source['title'][:60]}...")

    text, method_used = extract_text_for_source(conn, source, method)
    if not text:
        logger.warning(f"[{source['id']}] No text extracted")
        return False

    word_count = len(text.split())
    rel_path = save_extracted_text(source, text, method_used)

    update_source(conn, source["id"],
                  status="text_extracted",
                  extracted_text_path=rel_path,
                  word_count=word_count)

    logger.info(f"[{source['id']}] Extracted {word_count} words via {method_used} -> {rel_path}")
    return True


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Extract text from source documents")
    parser.add_argument("--source-id", type=int, help="Process a specific source")
    parser.add_argument("--method", choices=["pymupdf", "tesseract"], help="Force extraction method")
    parser.add_argument("--limit", type=int, help="Max sources to process")
    args = parser.parse_args()

    conn = init_db()

    if args.source_id:
        source = get_source_by_id(conn, args.source_id)
        if not source:
            logger.error(f"Source {args.source_id} not found")
            return
        process_source(conn, source, args.method)
    else:
        sources = get_sources_by_status(conn, "ingested")
        if not sources:
            logger.info("No sources pending text extraction")
            return

        if args.limit:
            sources = sources[:args.limit]

        logger.info(f"Processing {len(sources)} sources...")
        success = 0
        for source in sources:
            if process_source(conn, source, args.method):
                success += 1
        logger.info(f"Text extraction complete: {success}/{len(sources)} succeeded")

    conn.close()


if __name__ == "__main__":
    main()
