#!/usr/bin/env python3
"""Step 4: LLM-powered knowledge extraction.

Extracts from each source:
- Core theses and arguments
- Key concepts and definitions
- Empirical findings with data types and geography
- Critiques (with target author/work)
- Notable quotes
- Frameworks and theoretical models

Outputs:
- knowledge_items + concepts tables in DB
- knowledge/{source_id}.json structured output
- notes/readings/{author}_{title}.md reading note from template

Usage:
    python -m literature_pipeline.extract_knowledge [--source-id ID] [--limit N]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from .db import (
    get_connection, init_db, get_sources_by_status, get_source_by_id,
    update_source, insert_knowledge_item, get_or_create_concept,
    link_concept_source,
)
from .llm_backend import LLMBackend
from .utils import setup_logging, logger, PIPELINE_DIR, repo_root, sanitize_filename

KNOWLEDGE_DIR = PIPELINE_DIR / "knowledge"
EXTRACTED_DIR = PIPELINE_DIR / "extracted_text"


KNOWLEDGE_EXTRACTION_PROMPT = """You are an expert academic researcher. Analyze the following text from the source:

Title: {title}
Author(s): {authors}
Year: {year}

Extract the following structured knowledge. Be thorough but precise.

Return a JSON object with these keys:

1. "core_argument": A 2-3 sentence summary of the main thesis
2. "theses": Array of objects with {{content, confidence (0-1), page_range (if detectable)}}
3. "concepts": Array of objects with {{name (slug_format), display_name, definition, usage_type (introduces/uses/critiques/extends)}}
4. "definitions": Array of objects with {{term, definition, context}}
5. "empirical_findings": Array of objects with {{content, data_type, geography, confidence}}
6. "critiques": Array of objects with {{content, target_author, target_work, confidence}}
7. "frameworks": Array of objects with {{name, description, components}}
8. "quotes": Array of objects with {{text (exact quote), context, page_range}}
9. "evaluation": Object with {{epistemic (1-5), empirical (1-5), political (1-5), synthetic (1-5), notes}}
10. "tags": Array of relevant topic tags

TEXT:
{text}"""


def _read_extracted_text(source):
    """Read extracted text for a source."""
    text_path = source["extracted_text_path"]
    if not text_path:
        return None
    full_path = PIPELINE_DIR / text_path
    if not full_path.exists():
        return None
    text = full_path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    return text.strip()


def _parse_authors(source):
    """Get authors as a list."""
    authors = source["authors"]
    if isinstance(authors, str):
        try:
            authors = json.loads(authors)
        except (json.JSONDecodeError, TypeError):
            authors = [authors] if authors else []
    return authors or []


def extract_knowledge_llm(source, text, llm):
    """Use LLM to extract structured knowledge."""
    authors = _parse_authors(source)
    authors_str = ", ".join(authors) if authors else "Unknown"

    # Truncate to fit context window (keep beginning and end)
    max_chars = 30000
    if len(text) > max_chars:
        half = max_chars // 2
        text = text[:half] + "\n\n[...middle section truncated...]\n\n" + text[-half:]

    prompt = KNOWLEDGE_EXTRACTION_PROMPT.format(
        title=source["title"],
        authors=authors_str,
        year=source["year"] or "unknown",
        text=text,
    )

    return llm.complete_json(prompt, task="extract_knowledge", max_tokens=8192)


def save_knowledge_json(source_id, knowledge):
    """Save raw knowledge extraction as JSON."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = KNOWLEDGE_DIR / f"{source_id}.json"
    out_path.write_text(json.dumps(knowledge, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def store_knowledge_in_db(conn, source, knowledge):
    """Insert extracted knowledge items into the database."""
    source_id = source["id"]
    count = 0

    # Theses
    for item in knowledge.get("theses", []):
        insert_knowledge_item(
            conn, source_id=source_id, item_type="thesis",
            content=item.get("content", ""),
            confidence=item.get("confidence", 0.5),
            page_range=item.get("page_range"),
        )
        count += 1

    # Definitions
    for item in knowledge.get("definitions", []):
        insert_knowledge_item(
            conn, source_id=source_id, item_type="definition",
            content=f"{item.get('term', '')}: {item.get('definition', '')}",
            context=item.get("context"),
        )
        count += 1

    # Frameworks
    for item in knowledge.get("frameworks", []):
        insert_knowledge_item(
            conn, source_id=source_id, item_type="framework",
            content=item.get("description", item.get("name", "")),
            context=json.dumps(item.get("components", [])),
        )
        count += 1

    # Empirical findings
    for item in knowledge.get("empirical_findings", []):
        insert_knowledge_item(
            conn, source_id=source_id, item_type="empirical_finding",
            content=item.get("content", ""),
            confidence=item.get("confidence", 0.5),
            data_type=item.get("data_type"),
            geography=item.get("geography"),
        )
        count += 1

    # Critiques
    for item in knowledge.get("critiques", []):
        insert_knowledge_item(
            conn, source_id=source_id, item_type="critique",
            content=item.get("content", ""),
            confidence=item.get("confidence", 0.5),
            target_author=item.get("target_author"),
            target_work=item.get("target_work"),
        )
        count += 1

    # Quotes
    for item in knowledge.get("quotes", []):
        insert_knowledge_item(
            conn, source_id=source_id, item_type="quote",
            content=item.get("text", ""),
            context=item.get("context"),
            page_range=item.get("page_range"),
        )
        count += 1

    # Concepts → concepts table + concept_sources linking
    for item in knowledge.get("concepts", []):
        name = item.get("name", "").lower().replace(" ", "_")
        if not name:
            continue
        concept_id = get_or_create_concept(
            conn, name=name,
            display_name=item.get("display_name"),
            definition=item.get("definition"),
            first_source_id=source_id,
        )
        usage_type = item.get("usage_type", "uses")
        link_concept_source(conn, concept_id, source_id, usage_type)

    return count


def generate_reading_note(source, knowledge):
    """Generate a reading note following notes/templates/reading_note.md."""
    root = repo_root()
    readings_dir = root / "notes" / "readings"
    readings_dir.mkdir(parents=True, exist_ok=True)

    authors = _parse_authors(source)
    first_author = authors[0].split(",")[0].strip().lower() if authors else "unknown"
    title_slug = sanitize_filename(source["title"], max_len=40)
    filename = f"{first_author}_{title_slug}.md"
    out_path = readings_dir / filename

    authors_str = ", ".join(authors) if authors else "Unknown"
    evaluation = knowledge.get("evaluation", {})

    def stars(score):
        try:
            n = int(score)
        except (TypeError, ValueError):
            n = 0
        return "★" * n + "☆" * (5 - n)

    # Build concepts table
    concepts = knowledge.get("concepts", [])
    concepts_rows = ""
    for c in concepts:
        concepts_rows += f"| {c.get('display_name', c.get('name', ''))} | {c.get('definition', '')} | {c.get('usage_type', '')} |\n"
    if not concepts_rows:
        concepts_rows = "| | | |\n"

    # Build evidence
    findings = knowledge.get("empirical_findings", [])
    evidence_lines = ""
    for i, f in enumerate(findings, 1):
        geo = f" ({f['geography']})" if f.get("geography") else ""
        evidence_lines += f"- Finding {i}: {f.get('content', '')}{geo}\n"
    if not evidence_lines:
        evidence_lines = "- No empirical findings extracted\n"

    # Build quotes
    quotes = knowledge.get("quotes", [])
    quotes_section = ""
    for q in quotes:
        quotes_section += f"> {q.get('text', '')}\n\n"
    if not quotes_section:
        quotes_section = "> \n"

    # Build critiques
    critiques = knowledge.get("critiques", [])
    strengths = ""
    weaknesses = ""
    for cr in critiques:
        target = f" (re: {cr.get('target_author', '')})" if cr.get("target_author") else ""
        weaknesses += f"- {cr.get('content', '')}{target}\n"

    # Tags
    tags = knowledge.get("tags", [])
    tags_str = " ".join(f"#{t.replace(' ', '_')}" for t in tags)

    note = f"""# Reading Note: {source['title']}

## Source Information

**Author(s):** {authors_str}
**Title:** {source['title']}
**Year:** {source['year'] or 'unknown'}
**Publisher/Journal:** {source.get('publisher') or source.get('journal') or ''}
**Pages:**{f" {source['word_count']} words" if source.get('word_count') else ''}
**Language:** {source.get('language', 'en')}

**Status:** [x] Complete (auto-extracted)

## Evaluation

| Criterion | Score | Notes |
|-----------|-------|-------|
| Epistemic | {stars(evaluation.get('epistemic', 0))} | |
| Empirical | {stars(evaluation.get('empirical', 0))} | |
| Political | {stars(evaluation.get('political', 0))} | |
| Synthetic | {stars(evaluation.get('synthetic', 0))} | |

## Core Argument (2-3 sentences)

{knowledge.get('core_argument', 'Not extracted.')}

## Key Concepts

| Concept | Definition in Source | Your Assessment |
|---------|---------------------|-----------------|
{concepts_rows}
## Evidence & Cases

{evidence_lines}
## Relation to Our Project

**Direct relevance:** [ ] High / [ ] Medium / [ ] Low

**Connections to other sources:**
- Agrees with:
- Contradicts:
- Extends:

**Quotable passages:**
{quotes_section}
## Critical Assessment

**Strengths:**
{strengths or '- (review manually)'}

**Weaknesses:**
{weaknesses or '- (review manually)'}

**Questions it raises:**

**Questions it fails to address:**

## Tags

{tags_str}

---

*Created: {datetime.now().strftime('%Y-%m-%d')} (auto-extracted by literature pipeline)*
"""
    out_path.write_text(note, encoding="utf-8")
    logger.info(f"  Reading note: {out_path.relative_to(root)}")
    return out_path


def process_source(conn, source, llm):
    """Extract knowledge for a single source."""
    logger.info(f"[{source['id']}] Extracting knowledge: {source['title'][:60]}...")

    text = _read_extracted_text(source)
    if not text:
        logger.warning(f"[{source['id']}] No extracted text available")
        update_source(conn, source["id"], status="knowledge_extracted")
        return False

    try:
        knowledge = extract_knowledge_llm(source, text, llm)
    except Exception as e:
        logger.error(f"[{source['id']}] LLM extraction failed: {e}")
        return False

    # Save raw JSON
    save_knowledge_json(source["id"], knowledge)

    # Store in database
    count = store_knowledge_in_db(conn, source, knowledge)
    logger.info(f"[{source['id']}] Stored {count} knowledge items")

    # Generate reading note
    try:
        generate_reading_note(source, knowledge)
    except Exception as e:
        logger.warning(f"[{source['id']}] Reading note generation failed: {e}")

    # Update tags from extraction
    tags = knowledge.get("tags", [])
    if tags:
        update_source(conn, source["id"], tags=tags)

    update_source(conn, source["id"], status="knowledge_extracted")
    return True


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Extract knowledge from source texts")
    parser.add_argument("--source-id", type=int, help="Process a specific source")
    parser.add_argument("--limit", type=int, help="Max sources to process")
    args = parser.parse_args()

    conn = init_db()
    llm = LLMBackend()

    if args.source_id:
        source = get_source_by_id(conn, args.source_id)
        if not source:
            logger.error(f"Source {args.source_id} not found")
            return
        process_source(conn, source, llm)
    else:
        sources = get_sources_by_status(conn, "refs_extracted")
        if not sources:
            logger.info("No sources pending knowledge extraction")
            return

        if args.limit:
            sources = sources[:args.limit]

        logger.info(f"Processing {len(sources)} sources...")
        success = 0
        for source in sources:
            if process_source(conn, source, llm):
                success += 1
        logger.info(f"Knowledge extraction complete: {success}/{len(sources)} succeeded")

    conn.close()


if __name__ == "__main__":
    main()
