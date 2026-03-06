# Literature Pipeline — Agent Reference

This file is for AI agents working on or with the literature pipeline. Read this before modifying code or running commands.

## What This Is

A 7-step pipeline that processes academic literature (books, papers, journal articles) into a structured SQLite knowledge database. Source files (PDFs, ePubs) live externally. Only metadata, extracted text, and knowledge artifacts go into the git repo.

## Project Conventions

- **Python modules**: All files are part of the `literature_pipeline` package. Run as `python -m literature_pipeline.<module>` from the repo root, never directly with `python literature_pipeline/foo.py`.
- **Config**: `config.yaml` uses `${ENV_VAR:-default}` syntax, expanded at load time by `utils.py:_expand_env_vars()`.
- **Database**: SQLite at `literature_pipeline/literature.db` (gitignored). Initialize with `db.init_db()`. Always use `db.get_connection()` which sets WAL mode and foreign keys.
- **Logging**: Use `utils.setup_logging()` + `utils.logger`. Follows the same `[timestamp] message` pattern as `research/weekly_pipeline.py`.
- **LLM calls**: Always go through `llm_backend.LLMBackend`. Provider is selected by task name in config (`llm.tasks`). Never hardcode API keys — they come from env vars defined in `config.yaml`.

## Database Schema (7 tables)

```
sources                  — Core metadata, pipeline status tracking
extracted_references     — Bibliographic refs found in sources
citations                — Graph edges (citing → cited, with type)
knowledge_items          — Theses, definitions, empirical findings, critiques, quotes
concepts                 — Global concept registry
concept_sources          — Many-to-many: concept ↔ source with usage_type
embeddings               — RAG chunk metadata + paths to .npy files
```

**Pipeline status flow** on `sources.status`:
```
ingested → text_extracted → refs_extracted → knowledge_extracted → complete
```

Each step only picks up sources at its expected input status. Status is updated after successful processing.

## File Layout

| File | Role | Key functions |
|---|---|---|
| `db.py` | Schema + queries | `init_db()`, `insert_source()`, `update_source()`, `get_sources_by_status()`, `stats()` |
| `utils.py` | Config, logging, helpers | `load_config()`, `setup_logging()`, `file_hash()`, `sanitize_filename()` |
| `llm_backend.py` | LLM abstraction | `LLMBackend.complete()`, `.complete_json()`, `.embed()` |
| `ingest.py` | Step 1 | `ingest_single()`, `ingest_from_bibtex()`, `ingest_from_csv()`, `parse_bibtex()` |
| `extract_text.py` | Step 2 | `extract_pymupdf()`, `extract_tesseract()`, `extract_epub()`, `process_source()` |
| `extract_refs.py` | Step 3 | `extract_refs_grobid()`, `extract_refs_llm()`, `extract_refs_regex()` |
| `extract_knowledge.py` | Step 4 | `extract_knowledge_llm()`, `store_knowledge_in_db()`, `generate_reading_note()` |
| `build_graph.py` | Step 5 | `resolve_references()`, `export_json()`, `export_dot()` |
| `export_bib.py` | Step 6 | `export_to_bib()`, `import_from_bib()` |
| `generate_embeddings.py` | Step 7 | `chunk_text()`, `process_source()`, `search()` |
| `run_pipeline.py` | Orchestrator | Runs steps as subprocesses, supports `--dry-run`, `--from`, `--steps` |

## Integration Points — Don't Break These

1. **`literature/bibliography.bib`**: `export_bib.py` appends to a `% PIPELINE-ADDED ENTRIES` section. It NEVER modifies existing entries above that marker. `ingest.py --from-bibtex` reads it. The .bib uses sectioned comments (`% === SECTION NAME ===`).

2. **`notes/readings/*.md`**: `extract_knowledge.py` generates reading notes following the template at `notes/templates/reading_note.md`. The template has: Evaluation matrix (epistemic/empirical/political/synthetic stars), Core Argument, Key Concepts table, Evidence & Cases, Critical Assessment, Tags.

3. **`notes/concepts/`**: Cross-linked from knowledge extraction.

4. **`.gitignore`**: `literature_pipeline/embeddings/*.npy` and `literature_pipeline/literature.db` are gitignored.

## Common Tasks for Agents

### Adding a new extraction feature
1. Add the logic to the appropriate step module
2. If it touches the DB, add/migrate in `db.py` SCHEMA_SQL
3. Update the source's status field appropriately
4. Test: `python -m literature_pipeline.<module> --source-id <N>`

### Modifying the DB schema
- All DDL is in `db.py:SCHEMA_SQL` using `CREATE TABLE IF NOT EXISTS`
- Adding columns to existing tables requires `ALTER TABLE` migration logic
- Reference `research/scan_v5.py:connect_db()` for the migration pattern (check PRAGMA table_info, add column if missing)

### Changing LLM prompts
- Prompts live as module-level constants in `extract_refs.py` and `extract_knowledge.py`
- `complete_json()` appends a JSON-only instruction and strips markdown fences
- Test prompt changes with `--source-id` on a single source before bulk runs

### Adding a new LLM provider
1. Add config entry to `config.yaml` under `llm.providers`
2. If it's OpenAI-compatible (has `/v1/chat/completions`), it works automatically via the openai SDK path in `llm_backend.py`
3. If it needs a custom SDK, add a branch in `LLMBackend._get_client()` and `LLMBackend.complete()`

### Running the pipeline
```bash
# Dry run (no side effects)
python -m literature_pipeline.run_pipeline --dry-run

# Full run
python -m literature_pipeline.run_pipeline

# Single step
python -m literature_pipeline.run_pipeline --steps extract_knowledge

# Resume from a step
python -m literature_pipeline.run_pipeline --from extract_refs

# Limit to N sources per step
python -m literature_pipeline.run_pipeline --limit 3
```

## Dependencies

Not all are needed — only install what the current step requires:

| Package | Used by | Install |
|---|---|---|
| `pyyaml` | config loading | `pip install pyyaml` |
| `PyMuPDF` | PDF text extraction | `pip install PyMuPDF` |
| `pytesseract` + `pdf2image` | OCR for scans | `pip install pytesseract pdf2image` + system Tesseract |
| `EbookLib` + `beautifulsoup4` | ePub extraction | `pip install EbookLib beautifulsoup4` |
| `anthropic` | Claude LLM calls | `pip install anthropic` |
| `openai` | OpenAI/Kimi/Ollama calls + embeddings | `pip install openai` |
| `numpy` | Embedding storage + search | `pip install numpy` |
| `requests` | GROBID communication | `pip install requests` |

## Gotchas

- `authors` and `tags` are stored as JSON strings in SQLite. Always use `json.loads()` when reading, and `db.py` helpers handle serialization on write.
- `extracted_text_path` in `sources` is relative to `literature_pipeline/`, not the repo root.
- BibTeX import is idempotent — keyed on `bibtex_key` uniqueness. Running it twice is safe.
- GROBID extraction silently falls back to LLM if the service isn't running. No error, just a log line.
- `generate_embeddings.py` requires OpenAI API key even when using Claude for everything else — embeddings are OpenAI-only.
- The orchestrator (`run_pipeline.py`) runs each step as a subprocess. Steps don't share DB connections or LLM clients across process boundaries.
