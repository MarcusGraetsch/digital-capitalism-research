# Literature Processing & Knowledge Extraction Pipeline

Automated pipeline for processing academic sources (books, papers, journal articles) into a structured knowledge database. Handles the full path from scanned/digital PDFs through OCR, reference extraction, LLM-powered knowledge extraction, citation graph construction, and RAG embedding generation.

## Architecture

```
literature_pipeline/
├── config.yaml               # LLM providers, paths, extraction options
├── literature.db              # SQLite knowledge database (gitignored)
├── db.py                      # Schema (7 tables) + query helpers
├── llm_backend.py             # Multi-provider LLM abstraction
├── utils.py                   # Logging, config, hashing
│
├── ingest.py                  # Step 1: Register source metadata
├── extract_text.py            # Step 2: OCR / PDF / ePub text extraction
├── extract_refs.py            # Step 3: Reference extraction (GROBID + LLM)
├── extract_knowledge.py       # Step 4: LLM knowledge extraction
├── build_graph.py             # Step 5: Citation graph resolution + export
├── export_bib.py              # Step 6: Sync to bibliography.bib
├── generate_embeddings.py     # Step 7: RAG embeddings
├── run_pipeline.py            # Orchestrator
│
├── extracted_text/            # Markdown output per source
├── knowledge/                 # Structured JSON per source
└── embeddings/                # Numpy vectors (gitignored)
```

## Quick Start

```bash
# 1. Initialize DB and import existing bibliography
python -m literature_pipeline.ingest --from-bibtex literature/bibliography.bib

# 2. Ingest a single new source
python -m literature_pipeline.ingest \
  --file /path/to/book.pdf \
  --title "Platform Capitalism" \
  --authors "Srnicek, Nick" \
  --year 2017 \
  --type book

# 3. Run the full pipeline
python -m literature_pipeline.run_pipeline

# 4. Or run specific steps
python -m literature_pipeline.run_pipeline --steps extract_text,extract_refs

# 5. Check progress
python -m literature_pipeline.run_pipeline --stats
```

## Pipeline Steps

```
External PDF/ePub/scan
  → ingest.py            Register in sources table (status: ingested)
  → extract_text.py      OCR/parse → extracted_text/{id}.md (status: text_extracted)
  → extract_refs.py      GROBID or LLM → extracted_references table (status: refs_extracted)
  → extract_knowledge.py LLM → knowledge_items + concepts tables,
                          generates notes/readings/{author}_{title}.md
                          (status: knowledge_extracted)
  → build_graph.py       Resolve refs → citations table, export JSON/DOT
  → export_bib.py        Append new entries to literature/bibliography.bib
  → generate_embeddings.py  Chunk + embed → embeddings/*.npy (status: complete)
```

## Database Schema

**7 tables** in `literature.db` (SQLite):

| Table | Purpose |
|---|---|
| `sources` | Core metadata: title, authors, year, type, format, pipeline status, bibtex_key |
| `extracted_references` | Bibliographic refs found in sources (raw text, parsed fields, confidence) |
| `citations` | Graph edges: citing → cited, with context and type (supports/critiques/extends/mentions) |
| `knowledge_items` | Extracted knowledge: theses, definitions, frameworks, empirical findings, critiques, quotes |
| `concepts` | Global concept registry with definitions and categories |
| `concept_sources` | Many-to-many: which sources introduce/use/critique/extend which concepts |
| `embeddings` | RAG chunk metadata: chunk text, model, path to .npy vectors |

## Configuration

Edit `config.yaml` to set:

- **paths**: Source library location (external PDFs), repo root
- **llm.providers**: API keys (via env vars), models, base URLs for Claude, OpenAI, Kimi, Ollama
- **llm.tasks**: Which provider to use for each pipeline task
- **extraction**: PDF methods, GROBID URL, Tesseract language
- **embeddings**: Model, chunk size, overlap

Environment variables:
- `ANTHROPIC_API_KEY` — for Claude
- `OPENAI_API_KEY` — for OpenAI embeddings
- `LITERATURE_SOURCE_DIR` — override default source library path
- `RESEARCH_REPO` — override default repo root path

## LLM Backend

`llm_backend.py` provides a unified `LLMBackend` class with three methods:

- `complete(prompt, system, provider, task)` — text completion
- `complete_json(prompt, ...)` — completion expecting JSON response
- `embed(texts, provider, task)` — embedding generation (OpenAI-compatible only)

Supported providers:
- **Claude** — via `anthropic` SDK
- **OpenAI** — via `openai` SDK
- **Kimi** (Moonshot) — OpenAI-compatible with custom base_url
- **Ollama** — local models, OpenAI-compatible API

## Ingestion

```bash
# Single source
python -m literature_pipeline.ingest --file paper.pdf --title "Title" --authors "Last, First" --year 2024

# Bulk from BibTeX (idempotent — skips existing keys)
python -m literature_pipeline.ingest --from-bibtex literature/bibliography.bib --source-dir /path/to/pdfs

# Bulk from CSV (columns: title, authors, year, type, bibtex_key, file_path)
python -m literature_pipeline.ingest --from-csv sources.csv

# Show stats
python -m literature_pipeline.ingest --stats
```

## Text Extraction

Extraction methods (auto-selected by format):
- **PyMuPDF** — fast, for digital PDFs with embedded text
- **Tesseract OCR** — for scanned documents (auto-detected when PyMuPDF yields <100 chars/page)
- **ebooklib** — for ePub files

```bash
python -m literature_pipeline.extract_text                     # All pending
python -m literature_pipeline.extract_text --source-id 5       # Specific source
python -m literature_pipeline.extract_text --method tesseract  # Force OCR
```

## Reference Extraction

Tries methods in order:
1. **GROBID** — if Docker service is running at configured URL
2. **LLM** — sends bibliography section to Claude for structured parsing
3. **Regex** — basic Author (Year) pattern matching as last resort

```bash
python -m literature_pipeline.extract_refs
python -m literature_pipeline.extract_refs --method llm  # Force LLM
```

## Knowledge Extraction

LLM extracts from each source:
- Core argument summary
- Theses with confidence scores
- Key concepts with definitions
- Empirical findings (data type, geography)
- Critiques (target author/work)
- Notable quotes
- Evaluation scores (epistemic, empirical, political, synthetic)

Outputs:
- `knowledge/{source_id}.json` — raw structured extraction
- `notes/readings/{author}_{title}.md` — reading note following the project template

```bash
python -m literature_pipeline.extract_knowledge
python -m literature_pipeline.extract_knowledge --source-id 12
```

## Citation Graph

Resolves extracted references against known sources using fuzzy matching (author names, title similarity, year, DOI). Classifies citation types using knowledge items (e.g., critiques).

```bash
python -m literature_pipeline.build_graph                 # Resolve + export
python -m literature_pipeline.build_graph --export-only   # Just re-export
python -m literature_pipeline.build_graph --format dot    # Graphviz only
```

Exports: `knowledge/citation_graph.json`, `knowledge/citation_graph.dot`

## Bibliography Sync

Bidirectional sync with `literature/bibliography.bib`:
- **Export**: appends new DB sources to a `% PIPELINE-ADDED ENTRIES` section (never modifies existing entries)
- **Import**: reads .bib entries into the DB

```bash
python -m literature_pipeline.export_bib              # Export new entries
python -m literature_pipeline.export_bib --import     # Import .bib → DB
python -m literature_pipeline.export_bib --dry-run    # Preview
```

## RAG Embeddings

Chunks extracted text and generates embeddings via OpenAI's `text-embedding-3-small`. Includes a built-in semantic search.

```bash
python -m literature_pipeline.generate_embeddings
python -m literature_pipeline.generate_embeddings --search "platform capitalism and rent"
```

## Orchestrator

```bash
python -m literature_pipeline.run_pipeline                          # Full pipeline
python -m literature_pipeline.run_pipeline --dry-run                # Preview
python -m literature_pipeline.run_pipeline --from extract_knowledge # Resume from step
python -m literature_pipeline.run_pipeline --steps ingest,build_graph  # Specific steps
python -m literature_pipeline.run_pipeline --stats                  # DB statistics
python -m literature_pipeline.run_pipeline --limit 5                # Process max 5 sources per step
```

## Dependencies

Core (required):
- `pyyaml` — config loading

Per-feature (install as needed):
- `PyMuPDF` — PDF text extraction
- `pytesseract`, `pdf2image` — OCR (requires Tesseract system package)
- `EbookLib`, `beautifulsoup4` — ePub extraction
- `anthropic` — Claude API
- `openai` — OpenAI/Kimi/Ollama API
- `numpy` — embedding storage
- `requests` — GROBID communication
