#!/usr/bin/env python3
"""Database schema initialization and query helpers for literature.db."""

import json
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
"""


def get_connection(db_path=None):
    """Return a SQLite connection with WAL mode and foreign keys."""
    db_path = db_path or DB_FILE
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path=None):
    """Create all tables if they don't exist."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)
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
    return result


if __name__ == "__main__":
    conn = init_db()
    print("Database initialized successfully.")
    s = stats(conn)
    for k, v in s.items():
        print(f"  {k}: {v}")
    conn.close()
