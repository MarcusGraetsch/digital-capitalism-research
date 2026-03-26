# Digital Capitalism Research Project

A systematic, automated investigation of digital capitalism through continuous knowledge extraction and discourse mapping.

## What This Is

**Not a traditional research project.** This is a **continuous research infrastructure** that:
- Automatically scans ~20 newsletters daily for relevant articles
- Extracts and categorizes 1,104+ sources (and growing)
- Maps discourse networks: who cites whom, who critiques what
- Generates weekly research briefings via Telegram
- Maintains an interactive Knowledge Graph of concepts, tasks, and articles

**Philosophy:** Nachvollziehbarkeit meets automation. German academic rigor + modern data pipeline.

---

## Core Infrastructure

### 1. Literature Pipeline (`literature_pipeline/`)

**Automated ingestion from multiple sources:**
- 📧 **Email Link Aggregation**: 3 Gmail accounts scan newsletters (870+ articles extracted)
- 🎙️ **Podcast Pipeline**: Automatic transcription + summarization (5 tracked podcasts)
- 📚 **Academic Alerting**: OpenAlex API monitors 6+ key scholars (Zuboff, Srnicek, Harvey, etc.)
- 🔍 **Daily News Scan**: Multi-search-engine queries (17 engines, fallback strategy)

**Processing workflow:**
```
Ingest → Clean → Label (LLM) → Extract Knowledge → Update Ontology → Dashboard
```

### 2. Discourse Mapping System (NEW - March 2025)

**8 new database tables** tracking the conversation:
- **`persons`**: 49 seed scholars (Zuboff, Srnicek, Marx, Harvey...) with alias resolution
- **`works`**: Canonical bibliography (books, articles, reports)
- **`mentions`**: Who is cited where, with context (agreement/critique/discussion)
- **Citation network**: Visualize intellectual relationships

**Example queries:**
```bash
python -m literature_pipeline.discourse persons list
python -m literature_pipeline.discourse network person 3  # Zuboff's citation network
```

### 3. Knowledge Graph / Ontology (`memory/ontology/`)

**Interactive D3.js visualization** of:
- **12 Core Concepts**: Platform Capitalism, Surveillance Capitalism, Gig Economy, Green Colonialism...
- **7 Research Tasks**: Active chapters with deadlines and progress tracking
- **1,104+ Articles**: Linked to concepts and tasks
- **8,332+ Relationships**: `discusses_concept`, `related_by_tags`, `supports_task`

**Dashboard:** `ontology-dashboard.html` (auto-updates after each pipeline run)

### 4. Weekly Research Briefing

**Automated Telegram delivery** every Sunday 08:00:
- New articles this week (count + topics)
- Task progress updates
- Coverage gap analysis ("Topics with < 5 articles")
- Reading recommendation

---

## Repository Structure

```
.
├── README.md                           # This file
├── TODO.md                             # Active tasks
├── CRON_STATUS.md                      # Pipeline health monitoring
├── HEARTBEAT.md                        # Agent periodic tasks
├── 
├── literature_pipeline/                # Core ingestion system
│   ├── db.py                          # Database schema (8 new discourse tables)
│   ├── ingest.py                      # PDF processing
│   ├── discourse.py                   # NEW: Person/work/mention extraction
│   ├── quotes.py                      # Quote extraction
│   ├── extract_knowledge.py           # LLM-based knowledge extraction
│   └── telegram_handler.py            # Telegram bot integration
│
├── research/                          # News & article processing
│   ├── articles.db                    # Main database (1,104+ articles)
│   ├── scan_v5.py                     # Email link extraction
│   ├── scan_podcasts.py               # Podcast transcription pipeline
│   ├── scan_academic.py               # OpenLex academic monitoring
│   ├── extract_article_quotes.py      # Quote extraction from news
│   ├── weekly_pipeline.py             # Sunday newsletter processing
│   └── fulltext/                      # Extracted article content
│
├── memory/ontology/                   # Knowledge Graph
│   ├── schema.yaml                    # Ontology definition
│   ├── graph.jsonl                    # 8,332+ relationships
│   └── concepts/                      # Individual concept definitions
│
├── briefings/                         # Generated weekly reports
│   ├── latest.md                      # Current briefing
│   └── briefing_YYYYMMDD.md           # Archive
│
├── ontology-dashboard.html            # Interactive visualization
├── generate_weekly_briefing.py        # Briefing generator
└── update_dashboard.py                # Dashboard updater
```

---

## Key Statistics

| Metric | Count |
|--------|-------|
| **Articles collected** | 1,104+ |
| **Newsletter sources** | ~20 active |
| **Core concepts mapped** | 12 (6 digital capitalism + 6 environmental) |
| **Research tasks** | 7 active |
| **Tracked scholars** | 49 (with citation network) |
| **Database relationships** | 8,332+ |
| **Podcasts monitored** | 5 |
| **Academic authors tracked** | 6+ (OpenAlex API) |

---

## Automation Schedule

| Task | Frequency | Time (CET) |
|------|-----------|------------|
| Daily News Scan | Daily | 08:00 |
| Weekly Newsletter Processing | Sunday | 08:00 |
| Academic Paper Check | Weekly | With newsletter scan |
| Podcast Episode Scan | Weekly | With newsletter scan |
| Dashboard Update | After each pipeline | Automatic |
| Self-Improvement Report | Weekly | With newsletter scan |

---

## Key Concepts Tracked

### Digital Capitalism Core
- Platform Capitalism (Srnicek)
- Surveillance Capitalism (Zuboff)
- Gig Economy & Algorithmic Management
- Data Extractivism
- Precarious Work & Labor Organizing

### Environmental Dimension
- Digital Climate Impact
- Data Center Energy
- E-Waste & Critical Minerals
- Green Colonialism
- Environmental Justice

---

## Research Ethics & Transparency

**Nachvollziehbarkeit** (German academic rigor):
- All automation decisions documented in commits
- Process logs for every major article (`*.process.md`)
- Git history tracks all changes
- Source verification before inclusion (no hallucinated references)

**Human-AI Collaboration:**
- AI handles: Data extraction, categorization, pattern recognition
- Human handles: Interpretation, theoretical framing, ethical judgment
- Transparent about AI involvement in research process

---

## Current Status (March 2025)

**Phase:** Active data collection & discourse mapping

**Recent milestones:**
- ✅ Discourse mapping system deployed (49 scholars, citation networks)
- ✅ 1,104+ articles in database
- ✅ Weekly briefing automation active
- ✅ Knowledge Graph with interactive visualization
- ✅ Multi-source ingestion (email, RSS, academic, podcasts)
- ✅ Self-improvement logging established

**Next priorities:**
- [ ] Deep reading of Tier 1 sources (manual, ongoing)
- [ ] Citation network analysis (automated, in progress)
- [ ] Chapter drafting (Platform Capitalism theory)

---

## Quick Commands

```bash
# Check discourse stats
python -m literature_pipeline.discourse mentions stats

# List tracked scholars
python -m literature_pipeline.discourse persons list

# View citation network for a person
python -m literature_pipeline.discourse network person 3

# Run weekly pipeline manually
python research/weekly_pipeline.py

# Update dashboard
python update_dashboard.py

# Generate briefing
python generate_weekly_briefing.py
```

---

*Last updated: 2026-03-15 | See `memory/2026-03-15.md` for latest session log*
