#!/usr/bin/env python3
"""Database schema initialization and query helpers for literature.db."""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from .utils import PIPELINE_DIR, logger

DB_FILE = PIPELINE_DIR / "literature.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    authors         TEXT,           -- JSON array of author names
    year            INTEGER,
    type            TEXT,           -- book, paper, chapter, article, report, thesis
    format          TEXT,           -- pdf, epub, scan, html
    bibtex_key      TEXT UNIQUE,
    source_path     TEXT,           -- path to original file (external)
    status          TEXT DEFAULT 'ingested',
                                   -- ingested → text_extracted → refs_extracted
                                   --   → knowledge_extracted → complete
    extracted_text_path TEXT,       -- relative path in extracted_text/
    word_count      INTEGER,
    tags            TEXT,           -- JSON array
    priority        INTEGER DEFAULT 0,
    language        TEXT DEFAULT 'en',
    publisher       TEXT,
    journal         TEXT,
    doi             TEXT,
    isbn            TEXT,
    abstract        TEXT,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS extracted_references (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER NOT NULL REFERENCES sources(id),
    raw_text        TEXT,
    parsed_authors  TEXT,           -- JSON array
    parsed_title    TEXT,
    parsed_year     INTEGER,
    parsed_doi      TEXT,
    parsed_journal  TEXT,
    resolved_source_id INTEGER REFERENCES sources(id),
    extraction_method TEXT,         -- grobid, llm, regex
    confidence      REAL DEFAULT 0.0,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS citations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    citing_source_id INTEGER NOT NULL REFERENCES sources(id),
    cited_source_id  INTEGER NOT NULL REFERENCES sources(id),
    context         TEXT,           -- surrounding text of the citation
    citation_type   TEXT,           -- supports, critiques, extends, mentions
    page            TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(citing_source_id, cited_source_id)
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER NOT NULL REFERENCES sources(id),
    item_type       TEXT NOT NULL,  -- thesis, definition, framework, empirical_finding,
                                   --   critique, concept, quote
    content         TEXT NOT NULL,
    context         TEXT,
    page_range      TEXT,
    confidence      REAL DEFAULT 0.0,
    -- critique-specific
    target_author   TEXT,
    target_work     TEXT,
    -- empirical-specific
    data_type       TEXT,
    geography       TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS concepts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT UNIQUE NOT NULL,   -- slug: "platform_capitalism"
    display_name    TEXT,                    -- "Platform Capitalism"
    definition      TEXT,
    first_source_id INTEGER REFERENCES sources(id),
    related_concepts TEXT,                   -- JSON array of concept names
    category        TEXT,                    -- e.g. "economic", "political", "technological"
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS concept_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id      INTEGER NOT NULL REFERENCES concepts(id),
    source_id       INTEGER NOT NULL REFERENCES sources(id),
    usage_type      TEXT,           -- introduces, uses, critiques, extends
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(concept_id, source_id, usage_type)
);

CREATE TABLE IF NOT EXISTS embeddings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       INTEGER NOT NULL REFERENCES sources(id),
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding_model TEXT,
    embedding_path  TEXT,           -- path to .npy file
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_sources_bibtex ON sources(bibtex_key);
CREATE INDEX IF NOT EXISTS idx_refs_source ON extracted_references(source_id);
CREATE INDEX IF NOT EXISTS idx_refs_resolved ON extracted_references(resolved_source_id);
CREATE INDEX IF NOT EXISTS idx_citations_citing ON citations(citing_source_id);
CREATE INDEX IF NOT EXISTS idx_citations_cited ON citations(cited_source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_items(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_items(item_type);
CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name);
CREATE INDEX IF NOT EXISTS idx_concept_sources_concept ON concept_sources(concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_sources_source ON concept_sources(source_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_id);

CREATE TABLE IF NOT EXISTS quotes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    text            TEXT NOT NULL,           -- exact quote or paraphrased excerpt
    author          TEXT,                    -- who said/wrote it
    source_title    TEXT,                    -- book/article/podcast title
    source_year     INTEGER,
    page            TEXT,                    -- page number or range
    language        TEXT DEFAULT 'en',
    entry_type      TEXT NOT NULL,           -- 'quote' (verbatim) or 'excerpt' (paraphrase/summary)
    quote_type      TEXT,                    -- core_concept, polemic, critique, definition,
                                            --   aphorism, empirical, frequently_cited, programmatic
    topics          TEXT,                    -- JSON array of topic tags
    context         TEXT,                    -- why this matters, what debate it belongs to
    use_for         TEXT,                    -- JSON array: website, article, epigraph, social_media
    found_via       TEXT,                    -- literature_pipeline, news_article, podcast, manual
    pipeline_source_id INTEGER,             -- FK to sources(id) if from literature pipeline
    article_id      TEXT,                    -- ID from articles.db if from news pipeline
    episode_id      TEXT,                    -- ID from podcasts.db if from podcast pipeline
    rating          INTEGER DEFAULT 0,       -- 0-5, for manual curation
    used_count      INTEGER DEFAULT 0,       -- how often it has been used/published
    status          TEXT DEFAULT 'new',      -- new, curated, published, archived
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_quotes_author ON quotes(author);
CREATE INDEX IF NOT EXISTS idx_quotes_entry_type ON quotes(entry_type);
CREATE INDEX IF NOT EXISTS idx_quotes_quote_type ON quotes(quote_type);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_rating ON quotes(rating);
CREATE INDEX IF NOT EXISTS idx_quotes_source ON quotes(pipeline_source_id);

-- Discourse Mapping Tables

CREATE TABLE IF NOT EXISTS persons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name  TEXT NOT NULL,          -- "Zuboff, Shoshana"
    display_name    TEXT,                   -- "Shoshana Zuboff"
    sort_name       TEXT,                   -- "zuboff_shoshana" (lowercase, for dedup)
    birth_year      INTEGER,
    death_year      INTEGER,
    nationality     TEXT,
    affiliation     TEXT,                   -- current/last known institution
    role            TEXT,                   -- scholar, journalist, activist, politician, executive
    fields          TEXT,                   -- JSON array: ["surveillance_capitalism", "political_economy"]
    notes           TEXT,
    is_seed         INTEGER DEFAULT 0,      -- 1 = manually verified canonical entry
    merged_into_id  INTEGER REFERENCES persons(id),  -- soft-merge for dedup
    -- Citation metrics (fetched from OpenAlex / Semantic Scholar)
    works_count     INTEGER,
    cited_by_count  INTEGER,
    h_index         INTEGER,
    i10_index       INTEGER,
    mean_citedness_2yr REAL,
    metrics_source  TEXT,                   -- openalex, semantic_scholar
    metrics_updated_at TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_persons_sort ON persons(sort_name);
CREATE INDEX IF NOT EXISTS idx_persons_seed ON persons(is_seed);

CREATE TABLE IF NOT EXISTS person_aliases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL REFERENCES persons(id),
    alias           TEXT NOT NULL,          -- "S. Zuboff", "Zuboff, S."
    alias_sort      TEXT,                   -- normalized for matching
    alias_type      TEXT DEFAULT 'variant', -- variant, maiden_name, pseudonym, transliteration
    confidence      REAL DEFAULT 1.0,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(person_id, alias)
);
CREATE INDEX IF NOT EXISTS idx_aliases_sort ON person_aliases(alias_sort);

CREATE TABLE IF NOT EXISTS person_external_ids (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       INTEGER NOT NULL REFERENCES persons(id),
    id_type         TEXT NOT NULL,          -- orcid, gnd, viaf, openalex, wikidata
    external_id     TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(id_type, external_id)
);
CREATE INDEX IF NOT EXISTS idx_extids_person ON person_external_ids(person_id);

CREATE TABLE IF NOT EXISTS works (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_title TEXT NOT NULL,
    sort_title      TEXT,                   -- lowercase normalized
    work_type       TEXT,                   -- book, article, paper, report, chapter, speech, film
    year            INTEGER,
    language        TEXT DEFAULT 'en',
    publisher       TEXT,
    journal         TEXT,
    edition         TEXT,
    notes           TEXT,
    source_id       INTEGER REFERENCES sources(id),  -- FK if we have the actual source
    merged_into_id  INTEGER REFERENCES works(id),     -- soft-merge for dedup
    -- Citation metrics (fetched from OpenAlex / Semantic Scholar)
    cited_by_count  INTEGER,
    influential_citations INTEGER,
    citation_percentile REAL,
    fwci            REAL,                   -- field-weighted citation impact
    metrics_source  TEXT,                   -- openalex, semantic_scholar
    metrics_updated_at TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_works_sort ON works(sort_title);
CREATE INDEX IF NOT EXISTS idx_works_source ON works(source_id);

CREATE TABLE IF NOT EXISTS work_authors (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id         INTEGER NOT NULL REFERENCES works(id),
    person_id       INTEGER NOT NULL REFERENCES persons(id),
    role            TEXT DEFAULT 'author',  -- author, editor, translator, contributor
    position        INTEGER DEFAULT 0,     -- author ordering
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(work_id, person_id, role)
);
CREATE INDEX IF NOT EXISTS idx_workauthors_work ON work_authors(work_id);
CREATE INDEX IF NOT EXISTS idx_workauthors_person ON work_authors(person_id);

CREATE TABLE IF NOT EXISTS work_external_ids (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id         INTEGER NOT NULL REFERENCES works(id),
    id_type         TEXT NOT NULL,          -- doi, isbn, openalex, arxiv, url
    external_id     TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(id_type, external_id)
);
CREATE INDEX IF NOT EXISTS idx_workextids_work ON work_external_ids(work_id);

CREATE TABLE IF NOT EXISTS mentions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    -- WHERE the mention occurs (exactly one of these is set)
    source_id       INTEGER REFERENCES sources(id),      -- literature pipeline
    article_id      TEXT,                                  -- news articles.db
    episode_id      TEXT,                                  -- podcast
    -- WHAT is mentioned (at least one of these is set)
    mentioned_person_id  INTEGER REFERENCES persons(id),
    mentioned_work_id    INTEGER REFERENCES works(id),
    -- HOW it's mentioned
    mention_type    TEXT NOT NULL,          -- citation, discussion, critique, agreement,
                                           -- extension, application, name_drop, epigraph, data_source
    sentiment       TEXT,                   -- positive, negative, neutral, mixed
    significance    TEXT DEFAULT 'minor',   -- major (central to argument), moderate, minor (passing)
    context_text    TEXT,                   -- surrounding text / transcript snippet
    page_or_timestamp TEXT,                -- page range or timestamp in podcast
    -- Extraction metadata
    extraction_method TEXT,                 -- llm, grobid, regex, manual
    confidence      REAL DEFAULT 0.5,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_mentions_source ON mentions(source_id);
CREATE INDEX IF NOT EXISTS idx_mentions_article ON mentions(article_id);
CREATE INDEX IF NOT EXISTS idx_mentions_episode ON mentions(episode_id);
CREATE INDEX IF NOT EXISTS idx_mentions_person ON mentions(mentioned_person_id);
CREATE INDEX IF NOT EXISTS idx_mentions_work ON mentions(mentioned_work_id);
CREATE INDEX IF NOT EXISTS idx_mentions_type ON mentions(mention_type);
CREATE INDEX IF NOT EXISTS idx_mentions_significance ON mentions(significance);

CREATE TABLE IF NOT EXISTS mention_concepts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mention_id      INTEGER NOT NULL REFERENCES mentions(id),
    concept_id      INTEGER NOT NULL REFERENCES concepts(id),
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(mention_id, concept_id)
);
CREATE INDEX IF NOT EXISTS idx_mentionconcepts_mention ON mention_concepts(mention_id);
CREATE INDEX IF NOT EXISTS idx_mentionconcepts_concept ON mention_concepts(concept_id);

CREATE TABLE IF NOT EXISTS discovery_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    authors         TEXT,              -- JSON array
    year            INTEGER,
    abstract        TEXT,
    doi             TEXT,
    openalex_id     TEXT,
    s2_id           TEXT,
    open_access_url TEXT,
    journal         TEXT,
    cited_by_count  INTEGER,
    -- Discovery metadata
    discovered_via  TEXT NOT NULL,      -- refs_of:W123, cites:W456, author:A789, web:query, s2rec:W123
    discovered_from_work_id  INTEGER REFERENCES works(id),
    discovered_from_person_id INTEGER REFERENCES persons(id),
    -- LLM scoring
    relevance_score INTEGER,           -- 0-10
    novelty_score   INTEGER,           -- 0-10
    llm_verdict     TEXT,              -- accept, maybe, reject
    llm_reasoning   TEXT,              -- one-line explanation
    -- Status workflow
    status          TEXT DEFAULT 'pending_review',
                                       -- pending_review → accepted → ingested
                                       -- pending_review → rejected
                                       -- pending_review → deferred
    reviewed_at     TEXT,
    reviewer_notes  TEXT,
    -- Dedup
    title_hash      TEXT,              -- normalized title hash for dedup
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_discovery_title_hash ON discovery_queue(title_hash);
CREATE INDEX IF NOT EXISTS idx_discovery_status ON discovery_queue(status);
CREATE INDEX IF NOT EXISTS idx_discovery_relevance ON discovery_queue(relevance_score);
"""


def get_connection(db_path=None):
    """Return a SQLite connection with WAL mode and foreign keys."""
    db_path = db_path or DB_FILE
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS mentions_fts USING fts5(
    context_text,
    content='mentions',
    content_rowid='id'
);
"""

FTS_TRIGGERS_SQL = """
CREATE TRIGGER IF NOT EXISTS mentions_ai AFTER INSERT ON mentions BEGIN
    INSERT INTO mentions_fts(rowid, context_text) VALUES (new.id, new.context_text);
END;

CREATE TRIGGER IF NOT EXISTS mentions_ad AFTER DELETE ON mentions BEGIN
    INSERT INTO mentions_fts(mentions_fts, rowid, context_text) VALUES ('delete', old.id, old.context_text);
END;

CREATE TRIGGER IF NOT EXISTS mentions_au AFTER UPDATE OF context_text ON mentions BEGIN
    INSERT INTO mentions_fts(mentions_fts, rowid, context_text) VALUES ('delete', old.id, old.context_text);
    INSERT INTO mentions_fts(rowid, context_text) VALUES (new.id, new.context_text);
END;
"""


def _migrate_add_columns(conn):
    """Add new columns to existing tables (idempotent)."""
    migrations = [
        # Citation metrics on persons
        ("persons", "works_count", "INTEGER"),
        ("persons", "cited_by_count", "INTEGER"),
        ("persons", "h_index", "INTEGER"),
        ("persons", "i10_index", "INTEGER"),
        ("persons", "mean_citedness_2yr", "REAL"),
        ("persons", "metrics_source", "TEXT"),
        ("persons", "metrics_updated_at", "TEXT"),
        # Citation metrics on works
        ("works", "cited_by_count", "INTEGER"),
        ("works", "influential_citations", "INTEGER"),
        ("works", "citation_percentile", "REAL"),
        ("works", "fwci", "REAL"),
        ("works", "metrics_source", "TEXT"),
        ("works", "metrics_updated_at", "TEXT"),
    ]
    for table, column, col_type in migrations:
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    conn.commit()


def init_db(db_path=None):
    """Create all tables if they don't exist."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)
    # FTS5 virtual table and triggers (separate to avoid executescript issues)
    try:
        conn.executescript(FTS_SQL)
        conn.executescript(FTS_TRIGGERS_SQL)
    except Exception:
        pass  # FTS5 may not be available in all SQLite builds
    # Run column migrations for existing databases
    _migrate_add_columns(conn)
    conn.commit()
    logger.info(f"Database initialized: {db_path or DB_FILE}")
    return conn


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_sources_by_status(conn, status):
    """Return all sources with the given pipeline status."""
    return conn.execute(
        "SELECT * FROM sources WHERE status = ? ORDER BY priority DESC, id",
        (status,),
    ).fetchall()


def get_source_by_id(conn, source_id):
    """Return a single source by ID."""
    return conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()


def get_source_by_bibtex_key(conn, key):
    """Return a source by its BibTeX key."""
    return conn.execute(
        "SELECT * FROM sources WHERE bibtex_key = ?", (key,)
    ).fetchone()


def insert_source(conn, **kwargs):
    """Insert a new source, return its ID."""
    # Serialize JSON fields
    for field in ("authors", "tags"):
        if field in kwargs and isinstance(kwargs[field], (list, dict)):
            kwargs[field] = json.dumps(kwargs[field])

    kwargs.setdefault("status", "ingested")
    kwargs["created_at"] = datetime.now().isoformat()
    kwargs["updated_at"] = kwargs["created_at"]

    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?"] * len(kwargs))
    vals = list(kwargs.values())

    cursor = conn.execute(
        f"INSERT INTO sources ({cols}) VALUES ({placeholders})", vals
    )
    conn.commit()
    return cursor.lastrowid


def update_source(conn, source_id, **kwargs):
    """Update fields on a source."""
    for field in ("authors", "tags"):
        if field in kwargs and isinstance(kwargs[field], (list, dict)):
            kwargs[field] = json.dumps(kwargs[field])

    kwargs["updated_at"] = datetime.now().isoformat()
    assignments = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [source_id]
    conn.execute(f"UPDATE sources SET {assignments} WHERE id = ?", vals)
    conn.commit()


def insert_reference(conn, **kwargs):
    """Insert an extracted reference."""
    for field in ("parsed_authors",):
        if field in kwargs and isinstance(kwargs[field], (list, dict)):
            kwargs[field] = json.dumps(kwargs[field])

    kwargs["created_at"] = datetime.now().isoformat()
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?"] * len(kwargs))
    vals = list(kwargs.values())
    cursor = conn.execute(
        f"INSERT INTO extracted_references ({cols}) VALUES ({placeholders})", vals
    )
    conn.commit()
    return cursor.lastrowid


def insert_citation(conn, citing_id, cited_id, context=None, citation_type="mentions", page=None):
    """Insert a citation edge."""
    try:
        conn.execute(
            """INSERT OR IGNORE INTO citations
               (citing_source_id, cited_source_id, context, citation_type, page, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (citing_id, cited_id, context, citation_type, page, datetime.now().isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # duplicate


def insert_knowledge_item(conn, **kwargs):
    """Insert a knowledge item."""
    kwargs["created_at"] = datetime.now().isoformat()
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?"] * len(kwargs))
    vals = list(kwargs.values())
    cursor = conn.execute(
        f"INSERT INTO knowledge_items ({cols}) VALUES ({placeholders})", vals
    )
    conn.commit()
    return cursor.lastrowid


def get_or_create_concept(conn, name, display_name=None, definition=None,
                          first_source_id=None, category=None):
    """Return concept ID, creating if needed."""
    row = conn.execute("SELECT id FROM concepts WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cursor = conn.execute(
        """INSERT INTO concepts (name, display_name, definition, first_source_id, category, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, display_name, definition, first_source_id, category, datetime.now().isoformat()),
    )
    conn.commit()
    return cursor.lastrowid


def link_concept_source(conn, concept_id, source_id, usage_type="uses"):
    """Link a concept to a source."""
    try:
        conn.execute(
            """INSERT OR IGNORE INTO concept_sources (concept_id, source_id, usage_type, created_at)
               VALUES (?, ?, ?, ?)""",
            (concept_id, source_id, usage_type, datetime.now().isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass


def get_all_concepts(conn):
    """Return all concepts."""
    return conn.execute("SELECT * FROM concepts ORDER BY name").fetchall()


def search_sources(conn, query):
    """Simple text search across title and authors."""
    like = f"%{query}%"
    return conn.execute(
        "SELECT * FROM sources WHERE title LIKE ? OR authors LIKE ? ORDER BY year DESC",
        (like, like),
    ).fetchall()


def insert_quote(conn, **kwargs):
    """Insert a quote or excerpt."""
    for field in ("topics", "use_for"):
        if field in kwargs and isinstance(kwargs[field], (list, dict)):
            kwargs[field] = json.dumps(kwargs[field])

    kwargs["created_at"] = datetime.now().isoformat()
    kwargs["updated_at"] = kwargs["created_at"]

    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?"] * len(kwargs))
    vals = list(kwargs.values())
    cursor = conn.execute(
        f"INSERT INTO quotes ({cols}) VALUES ({placeholders})", vals
    )
    conn.commit()
    return cursor.lastrowid


def quote_exists(conn, text, author=None):
    """Check if a similar quote already exists (exact text match)."""
    if author:
        row = conn.execute(
            "SELECT id FROM quotes WHERE text = ? AND author = ?", (text, author)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM quotes WHERE text = ?", (text,)
        ).fetchone()
    return row is not None


def get_quotes(conn, entry_type=None, quote_type=None, status=None,
               min_rating=None, author=None, limit=50):
    """Query quotes with optional filters."""
    conditions = []
    params = []

    if entry_type:
        conditions.append("entry_type = ?")
        params.append(entry_type)
    if quote_type:
        conditions.append("quote_type = ?")
        params.append(quote_type)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if min_rating is not None:
        conditions.append("rating >= ?")
        params.append(min_rating)
    if author:
        conditions.append("author LIKE ?")
        params.append(f"%{author}%")

    where = " AND ".join(conditions) if conditions else "1=1"
    params.append(limit)

    return conn.execute(
        f"SELECT * FROM quotes WHERE {where} ORDER BY rating DESC, created_at DESC LIMIT ?",
        params,
    ).fetchall()


def update_quote(conn, quote_id, **kwargs):
    """Update fields on a quote."""
    for field in ("topics", "use_for"):
        if field in kwargs and isinstance(kwargs[field], (list, dict)):
            kwargs[field] = json.dumps(kwargs[field])

    kwargs["updated_at"] = datetime.now().isoformat()
    assignments = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [quote_id]
    conn.execute(f"UPDATE quotes SET {assignments} WHERE id = ?", vals)
    conn.commit()


# ---------------------------------------------------------------------------
# Discourse mapping helpers
# ---------------------------------------------------------------------------

def _normalize_person_name(name):
    """Normalize a person name to sort_name format: 'zuboff_shoshana'."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    # Handle "Last, First" → "last first"
    parts = [p.strip() for p in name.split(",", 1)]
    if len(parts) == 2:
        name = f"{parts[0]} {parts[1]}"
    name = re.sub(r"\s+", "_", name.strip())
    return name


def _generate_aliases(canonical_name):
    """Generate standard name variants from canonical 'Last, First' format."""
    aliases = set()
    aliases.add(canonical_name)

    parts = [p.strip() for p in canonical_name.split(",", 1)]
    if len(parts) == 2:
        last, first = parts
        # "Shoshana Zuboff"
        aliases.add(f"{first} {last}")
        # "S. Zuboff"
        if first:
            aliases.add(f"{first[0]}. {last}")
        # "Zuboff, S."
        if first:
            aliases.add(f"{last}, {first[0]}.")
    return aliases


def resolve_person_name(conn, name):
    """Look up a person by name, checking aliases and sort_name.

    Returns person row (following merged_into_id) or None.
    """
    sort = _normalize_person_name(name)

    # Exact sort_name match
    row = conn.execute(
        "SELECT * FROM persons WHERE sort_name = ? AND merged_into_id IS NULL",
        (sort,),
    ).fetchone()
    if row:
        return row

    # Alias match
    row = conn.execute(
        """SELECT p.* FROM persons p
           JOIN person_aliases pa ON pa.person_id = p.id
           WHERE pa.alias_sort = ? AND p.merged_into_id IS NULL""",
        (sort,),
    ).fetchone()
    if row:
        return row

    # Fuzzy: check if sort_name starts with the same last-name token
    last_token = sort.split("_")[0] if "_" in sort else sort
    candidates = conn.execute(
        "SELECT * FROM persons WHERE sort_name LIKE ? AND merged_into_id IS NULL",
        (f"{last_token}%",),
    ).fetchall()

    if len(candidates) == 1:
        return candidates[0]

    return None


def get_or_create_person(conn, name, **kwargs):
    """Resolve or create a person. Returns person ID.

    Tries alias resolution first; creates new entry if no match found.
    """
    existing = resolve_person_name(conn, name)
    if existing:
        return existing["id"]

    # Determine canonical_name format
    canonical = name.strip()
    # If given as "First Last", flip to "Last, First"
    if "," not in canonical:
        parts = canonical.rsplit(" ", 1)
        if len(parts) == 2:
            canonical = f"{parts[1]}, {parts[0]}"

    sort = _normalize_person_name(canonical)

    # Serialize JSON fields
    for field in ("fields",):
        if field in kwargs and isinstance(kwargs[field], (list, dict)):
            kwargs[field] = json.dumps(kwargs[field])

    now = datetime.now().isoformat()
    cursor = conn.execute(
        """INSERT INTO persons (canonical_name, display_name, sort_name,
           birth_year, death_year, nationality, affiliation, role, fields,
           notes, is_seed, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            canonical,
            kwargs.get("display_name") or name.strip(),
            sort,
            kwargs.get("birth_year"),
            kwargs.get("death_year"),
            kwargs.get("nationality"),
            kwargs.get("affiliation"),
            kwargs.get("role"),
            kwargs.get("fields"),
            kwargs.get("notes"),
            kwargs.get("is_seed", 0),
            now, now,
        ),
    )
    person_id = cursor.lastrowid

    # Generate and store aliases
    for alias in _generate_aliases(canonical):
        try:
            conn.execute(
                """INSERT OR IGNORE INTO person_aliases
                   (person_id, alias, alias_sort, alias_type, created_at)
                   VALUES (?, ?, ?, 'variant', ?)""",
                (person_id, alias, _normalize_person_name(alias), now),
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()

    # Fetch citation metrics inline (non-blocking)
    if kwargs.get("fetch_metrics", True):
        try:
            from .fetch_metrics import fetch_metrics_for_new_person
            fetch_metrics_for_new_person(conn, person_id)
        except Exception:
            pass  # Network errors shouldn't break person creation

    return person_id


def _normalize_title(title):
    """Normalize a title for matching."""
    title = title.lower().strip()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", "_", title.strip())
    return title


def get_or_create_work(conn, title, authors=None, year=None, **kwargs):
    """Resolve or create a work. Returns work ID.

    Matches on sort_title + year, or source_id if provided.
    """
    sort = _normalize_title(title)

    # Check for existing by sort_title + year
    if year:
        row = conn.execute(
            "SELECT * FROM works WHERE sort_title = ? AND year = ? AND merged_into_id IS NULL",
            (sort, year),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM works WHERE sort_title = ? AND merged_into_id IS NULL",
            (sort,),
        ).fetchone()
    if row:
        return row["id"]

    # Check by source_id
    if kwargs.get("source_id"):
        row = conn.execute(
            "SELECT * FROM works WHERE source_id = ? AND merged_into_id IS NULL",
            (kwargs["source_id"],),
        ).fetchone()
        if row:
            return row["id"]

    now = datetime.now().isoformat()
    cursor = conn.execute(
        """INSERT INTO works (canonical_title, sort_title, work_type, year,
           language, publisher, journal, edition, notes, source_id, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            title.strip(),
            sort,
            kwargs.get("work_type"),
            year,
            kwargs.get("language", "en"),
            kwargs.get("publisher"),
            kwargs.get("journal"),
            kwargs.get("edition"),
            kwargs.get("notes"),
            kwargs.get("source_id"),
            now, now,
        ),
    )
    work_id = cursor.lastrowid

    # Link authors if provided
    if authors:
        if isinstance(authors, str):
            try:
                authors = json.loads(authors)
            except (json.JSONDecodeError, TypeError):
                authors = [authors]
        for i, author_name in enumerate(authors):
            person_id = get_or_create_person(conn, author_name)
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO work_authors
                       (work_id, person_id, role, position, created_at)
                       VALUES (?, ?, 'author', ?, ?)""",
                    (work_id, person_id, i, now),
                )
            except sqlite3.IntegrityError:
                pass

    conn.commit()

    # Fetch citation metrics inline (non-blocking)
    if kwargs.get("fetch_metrics", True):
        try:
            from .fetch_metrics import fetch_metrics_for_new_work
            fetch_metrics_for_new_work(conn, work_id)
        except Exception:
            pass  # Network errors shouldn't break work creation

    return work_id


def insert_mention(conn, **kwargs):
    """Insert a mention record. Returns mention ID."""
    kwargs["created_at"] = datetime.now().isoformat()
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join(["?"] * len(kwargs))
    vals = list(kwargs.values())
    cursor = conn.execute(
        f"INSERT INTO mentions ({cols}) VALUES ({placeholders})", vals
    )
    conn.commit()
    return cursor.lastrowid


def find_duplicate_persons(conn, threshold=0.8):
    """Find potential duplicate persons based on similar sort_names."""
    persons = conn.execute(
        "SELECT * FROM persons WHERE merged_into_id IS NULL ORDER BY sort_name"
    ).fetchall()

    duplicates = []
    for i, p1 in enumerate(persons):
        for p2 in persons[i + 1:]:
            s1, s2 = p1["sort_name"] or "", p2["sort_name"] or ""
            # Simple prefix match
            if s1 and s2 and (s1.startswith(s2.split("_")[0]) or s2.startswith(s1.split("_")[0])):
                if s1 != s2:
                    duplicates.append((p1, p2))
    return duplicates


def merge_persons(conn, keep_id, merge_id):
    """Soft-merge: redirect merge_id into keep_id."""
    now = datetime.now().isoformat()

    # Transfer aliases
    conn.execute(
        "UPDATE OR IGNORE person_aliases SET person_id = ? WHERE person_id = ?",
        (keep_id, merge_id),
    )
    # Transfer work_authors
    conn.execute(
        "UPDATE OR IGNORE work_authors SET person_id = ? WHERE person_id = ?",
        (keep_id, merge_id),
    )
    # Transfer mentions
    conn.execute(
        "UPDATE mentions SET mentioned_person_id = ? WHERE mentioned_person_id = ?",
        (keep_id, merge_id),
    )
    # Transfer external IDs
    conn.execute(
        "UPDATE OR IGNORE person_external_ids SET person_id = ? WHERE person_id = ?",
        (keep_id, merge_id),
    )
    # Mark as merged
    conn.execute(
        "UPDATE persons SET merged_into_id = ?, updated_at = ? WHERE id = ?",
        (keep_id, now, merge_id),
    )
    conn.commit()


def get_person_mentions(conn, person_id):
    """Get all mentions of a person across all pipelines."""
    return conn.execute(
        """SELECT m.*, s.title as source_title
           FROM mentions m
           LEFT JOIN sources s ON s.id = m.source_id
           WHERE m.mentioned_person_id = ?
           ORDER BY m.significance DESC, m.created_at DESC""",
        (person_id,),
    ).fetchall()


def get_work_mentions(conn, work_id):
    """Get all mentions of a work across all pipelines."""
    return conn.execute(
        """SELECT m.*, s.title as source_title
           FROM mentions m
           LEFT JOIN sources s ON s.id = m.source_id
           WHERE m.mentioned_work_id = ?
           ORDER BY m.significance DESC, m.created_at DESC""",
        (work_id,),
    ).fetchall()


def get_discourse_network(conn, person_id):
    """Get the discourse network for a person: who cites/discusses them."""
    return conn.execute(
        """SELECT
               p.id, p.canonical_name, p.display_name,
               m.mention_type, m.sentiment, m.significance,
               COUNT(*) as mention_count,
               s.title as source_title, s.id as source_id
           FROM mentions m
           JOIN sources s ON s.id = m.source_id
           JOIN work_authors wa ON wa.work_id IS NOT NULL
           JOIN persons p ON p.id = wa.person_id
           WHERE m.mentioned_person_id = ?
             AND s.id IS NOT NULL
           GROUP BY p.id, m.mention_type
           ORDER BY mention_count DESC""",
        (person_id,),
    ).fetchall()


def stats(conn):
    """Return pipeline statistics."""
    result = {}
    result["total_sources"] = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    for status in ("ingested", "text_extracted", "refs_extracted", "knowledge_extracted", "complete"):
        result[status] = conn.execute(
            "SELECT COUNT(*) FROM sources WHERE status = ?", (status,)
        ).fetchone()[0]
    result["total_references"] = conn.execute("SELECT COUNT(*) FROM extracted_references").fetchone()[0]
    result["total_citations"] = conn.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    result["total_knowledge_items"] = conn.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0]
    result["total_concepts"] = conn.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
    result["total_quotes"] = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    result["quotes_curated"] = conn.execute(
        "SELECT COUNT(*) FROM quotes WHERE status = 'curated'"
    ).fetchone()[0]
    # Discourse mapping stats
    result["total_persons"] = conn.execute("SELECT COUNT(*) FROM persons WHERE merged_into_id IS NULL").fetchone()[0]
    result["seed_persons"] = conn.execute("SELECT COUNT(*) FROM persons WHERE is_seed = 1").fetchone()[0]
    result["total_works"] = conn.execute("SELECT COUNT(*) FROM works WHERE merged_into_id IS NULL").fetchone()[0]
    result["total_mentions"] = conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
    result["persons_with_metrics"] = conn.execute(
        "SELECT COUNT(*) FROM persons WHERE cited_by_count IS NOT NULL AND merged_into_id IS NULL"
    ).fetchone()[0]
    result["works_with_metrics"] = conn.execute(
        "SELECT COUNT(*) FROM works WHERE cited_by_count IS NOT NULL AND merged_into_id IS NULL"
    ).fetchone()[0]
    # Discovery queue stats
    try:
        result["discovery_pending"] = conn.execute(
            "SELECT COUNT(*) FROM discovery_queue WHERE status = 'pending_review'"
        ).fetchone()[0]
        result["discovery_accepted"] = conn.execute(
            "SELECT COUNT(*) FROM discovery_queue WHERE status = 'accepted'"
        ).fetchone()[0]
        result["discovery_total"] = conn.execute(
            "SELECT COUNT(*) FROM discovery_queue"
        ).fetchone()[0]
    except Exception:
        pass  # Table may not exist yet
    return result


if __name__ == "__main__":
    conn = init_db()
    print("Database initialized successfully.")
    s = stats(conn)
    for k, v in s.items():
        print(f"  {k}: {v}")
    conn.close()
