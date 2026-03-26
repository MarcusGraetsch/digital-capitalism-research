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
├── telegram_handler.py        # Telegram Integration (PDF via Chat)
├── inbox/                     # Eingehende PDFs von Telegram
│   ├── monograph/
│   ├── edited_volume/
│   ├── journal_article/
│   └── web_article/
├── archive/                   # Archivierte PDFs für RAG
│   ├── monograph/
│   ├── edited_volume/
│   ├── journal_article/
│   └── web_article/
│
├── extracted_text/            # Markdown output per source
├── knowledge/                 # Structured JSON per source
└── embeddings/                # Numpy vectors (gitignored)
```

## Quick Start

```bash
# Initialize database
python -m literature_pipeline.db

# Run full pipeline
python -m literature_pipeline.run_pipeline

# Or step by step
python -m literature_pipeline.ingest --file paper.pdf --title "Title"
python -m literature_pipeline.extract_text --source-id 1
python -m literature_pipeline.extract_refs --source-id 1
python -m literature_pipeline.extract_knowledge --source-id 1
```

## Steps

### 1. Ingest — Register Sources

```bash
# Single PDF
python -m literature_pipeline.ingest --file path/to.pdf --title "Title" --authors "Author"

# From BibTeX
python -m literature_pipeline.ingest --from-bibtex ../literature/bibliography.bib

# From CSV
python -m literature_pipeline.ingest --from-csv sources.csv
```

### 2. Extract Text

```bash
python -m literature_pipeline.extract_text           # All pending sources
python -m literature_pipeline.extract_text --source-id 1   # Single source
python -m literature_pipeline.extract_text --ocr     # Force OCR (for scans)
```

Supports:
- PDF (text layer or OCR via Tesseract)
- ePub (preserves structure)
- Images (OCR)

### 3. Extract References

```bash
python -m literature_pipeline.extract_refs --source-id 1
```

Uses GROBID service if available, falls back to LLM parsing.

### 4. Extract Knowledge

```bash
python -m literature_pipeline.extract_knowledge --source-id 1
```

LLM extracts:
- Core arguments & claims
- Key concepts
- Empirical evidence
- Critical assessments
- Quotes with context

Outputs to `knowledge/{source_id}.json` and generates reading notes.

### 5. Build Citation Graph

```bash
python -m literature_pipeline.build_graph --export-dot
python -m literature_pipeline.build_graph --export-json
```

Resolves references to known sources, exports graph formats.

### 6. Export Bibliography

```bash
python -m literature_pipeline.export_bib              # Export to bibliography.bib
python -m literature_pipeline.export_bib --from-bibtex ../literature/bib.bib  # Sync back
```

### 7. RAG Embeddings

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

## Telegram Integration

Sende PDFs direkt via Telegram an die Pipeline. Rook (OpenClaw Agent) verarbeitet sie automatisch und sendet eine Zusammenfassung zurück.

### Publikationstypen

Die Pipeline unterscheidet automatisch zwischen:

| Typ | Emoji | Beschreibung | Archiv-Unterordner |
|-----|-------|--------------|-------------------|
| **monograph** | 📚 | Einzelwerk/Buch (ein Autor, ein Werk) | `archive/monograph/` |
| **edited_volume** | 📖 | Sammelband (Herausgeber, mehrere Artikel) | `archive/edited_volume/` |
| **journal_article** | 📄 | Zeitschriftenartikel (Journal, Issue, Pages) | `archive/journal_article/` |
| **web_article** | 🌐 | Wissenschaftlicher Online-Artikel / Preprint | `archive/web_article/` |

### Typ-Erkennung

Der Typ wird automatisch erkannt aus:
- **Filename**: Keywords wie "edited by", "journal", "vol.", "arxiv"
- **Text-Sample**: Erste Seite wird nach typischen Mustern gescannt
- **Manuell**: Optional als Parameter übergebbar

### Workflow

```
Du (Telegram) → PDF senden → Typ-Erkennung → Rook speichert in inbox/{type}/
                                      ↓
                    Typ-spezifische Pipeline:
                    - monograph: alle Schritte + alle Referenzen
                    - edited_volume: alle Schritte + Kapitel-Extraktion
                    - journal_article: alle Schritte + Journal-Metadaten
                    - web_article: KEINE Referenz-Extraktion (meist externe Links)
                                      ↓
                    Zusammenfassung: Titel + Typ-spezifische Metadaten + Key Findings
                                      ↓
                    + 3 Beispiel-Referenzen (nur Monograph/Edited Volume)
                                      ↓
                    + 3 BibTeX-Einträge
                                      ↓
                    Antwort an Dich (Telegram)
```

### Ausgabe-Format (typ-spezifisch)

**Monograph:**
```
📚 *Titel*
👤 Autor
🏛 Verlag
📅 Jahr

📝 *Key Findings:*
...

📚 *Beispiel-Referenzen:*
...
```

**Journal Article:**
```
📄 *Titel*
👤 Autor
📰 Journal, Vol. X, Issue Y, pp. Z, Jahr

📝 *Abstract:*
...
```

**Web Article:**
```
🌐 *Titel*
👤 Autor
📅 Jahr
🔗 URL...

📝 *Abstract:*
...
```

### Verzeichnisstruktur

```
inbox/
├── monograph/           # Eingehende Monographien
├── edited_volume/       # Eingehende Sammelbände
├── journal_article/     # Eingehende Zeitschriftenartikel
└── web_article/         # Eingehende Online-Artikel

archive/                 # Langzeitarchivierung (für RAG)
├── monograph/
├── edited_volume/
├── journal_article/
└── web_article/
```

### Technische Details

Das Modul `telegram_handler.py`:
- Wird von OpenClaw aufgerufen (nicht manuell)
- `detect_publication_type()`: Erkennt Typ aus Filename/Text
- Typ-spezifische Verarbeitung (z.B. web_article ohne Ref-Extraktion)
- Archiviert PDFs mit Präfix: `{type}_source_{id}_...`
- Formatiert Ausgabe Telegram-Markdown-kompatibel

### Manuelle Tests (nur für Entwicklung)

```bash
# Test mit lokaler PDF-Datei (Typ wird automatisch erkannt)
python -m literature_pipeline.telegram_handler --test-file paper.pdf

# Mit explizitem Typ
python -m literature_pipeline.telegram_handler --test-file article.pdf --type journal_article
```

---

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
