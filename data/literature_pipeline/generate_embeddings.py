#!/usr/bin/env python3
"""Step 7: Generate RAG embeddings for extracted texts.

Chunks each source's extracted text and generates embeddings via OpenAI API.
Stores vectors as .npy files and metadata in the embeddings table.

Usage:
    python -m literature_pipeline.generate_embeddings [--source-id ID] [--limit N]
    python -m literature_pipeline.generate_embeddings --search "platform capitalism"
"""

import argparse
import json
from pathlib import Path

import numpy as np

from .db import get_connection, init_db, get_sources_by_status, get_source_by_id, update_source
from .llm_backend import LLMBackend
from .utils import setup_logging, logger, PIPELINE_DIR, load_config

EMBEDDINGS_DIR = PIPELINE_DIR / "embeddings"
EXTRACTED_DIR = PIPELINE_DIR / "extracted_text"


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


def chunk_text(text, chunk_size=512, overlap=64):
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def process_source(conn, source, llm, config):
    """Generate embeddings for a single source."""
    logger.info(f"[{source['id']}] Generating embeddings: {source['title'][:60]}...")

    text = _read_extracted_text(source)
    if not text:
        logger.warning(f"[{source['id']}] No extracted text")
        return False

    emb_config = config.get("embeddings", {})
    chunk_size = emb_config.get("chunk_size", 512)
    chunk_overlap = emb_config.get("chunk_overlap", 64)
    model = emb_config.get("model", "text-embedding-3-small")

    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        logger.warning(f"[{source['id']}] No chunks generated")
        return False

    logger.info(f"[{source['id']}] {len(chunks)} chunks, embedding...")

    # Batch embed (OpenAI allows up to ~2048 inputs)
    batch_size = 100
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        try:
            vectors = llm.embed(batch, task="generate_embeddings")
            all_embeddings.extend(vectors)
        except Exception as e:
            logger.error(f"[{source['id']}] Embedding failed at batch {i}: {e}")
            return False

    # Save as numpy array
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    arr = np.array(all_embeddings, dtype=np.float32)
    npy_path = EMBEDDINGS_DIR / f"{source['id']}.npy"
    np.save(npy_path, arr)

    # Store chunk metadata in DB
    rel_path = str(npy_path.relative_to(PIPELINE_DIR))
    for idx, chunk in enumerate(chunks):
        conn.execute(
            """INSERT INTO embeddings (source_id, chunk_index, chunk_text, embedding_model, embedding_path, created_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))""",
            (source["id"], idx, chunk[:500], model, rel_path),
        )
    conn.commit()

    update_source(conn, source["id"], status="complete")
    logger.info(f"[{source['id']}] Saved {len(chunks)} embeddings -> {rel_path}")
    return True


def search(conn, query, llm, top_k=10):
    """Semantic search across all embedded sources."""
    # Embed the query
    query_vec = llm.embed([query], task="generate_embeddings")[0]
    query_vec = np.array(query_vec, dtype=np.float32)

    # Load all embedding files
    results = []

    source_ids = conn.execute(
        "SELECT DISTINCT source_id FROM embeddings"
    ).fetchall()

    for row in source_ids:
        sid = row["source_id"]
        npy_path = EMBEDDINGS_DIR / f"{sid}.npy"
        if not npy_path.exists():
            continue

        arr = np.load(npy_path)
        # Cosine similarity
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1
        normalized = arr / norms
        query_norm = query_vec / (np.linalg.norm(query_vec) or 1)
        similarities = normalized @ query_norm

        # Get top chunk for this source
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        # Get chunk text
        chunk_row = conn.execute(
            "SELECT chunk_text FROM embeddings WHERE source_id = ? AND chunk_index = ?",
            (sid, best_idx),
        ).fetchone()

        source = conn.execute("SELECT * FROM sources WHERE id = ?", (sid,)).fetchone()

        results.append({
            "source_id": sid,
            "title": source["title"] if source else "?",
            "year": source["year"] if source else None,
            "score": best_score,
            "chunk": chunk_row["chunk_text"] if chunk_row else "",
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Generate RAG embeddings")
    parser.add_argument("--source-id", type=int, help="Process a specific source")
    parser.add_argument("--limit", type=int, help="Max sources to process")
    parser.add_argument("--search", help="Semantic search query")
    args = parser.parse_args()

    config = load_config()
    conn = init_db()
    llm = LLMBackend(config)

    if args.search:
        results = search(conn, args.search, llm)
        if not results:
            print("No results found.")
        else:
            for i, r in enumerate(results, 1):
                print(f"\n{i}. [{r['score']:.3f}] {r['title']} ({r['year']})")
                print(f"   {r['chunk'][:200]}...")
        conn.close()
        return

    if args.source_id:
        source = get_source_by_id(conn, args.source_id)
        if not source:
            logger.error(f"Source {args.source_id} not found")
            return
        process_source(conn, source, llm, config)
    else:
        sources = get_sources_by_status(conn, "knowledge_extracted")
        if not sources:
            logger.info("No sources pending embedding generation")
            return

        if args.limit:
            sources = sources[:args.limit]

        logger.info(f"Processing {len(sources)} sources...")
        success = 0
        for source in sources:
            if process_source(conn, source, llm, config):
                success += 1
        logger.info(f"Embedding generation complete: {success}/{len(sources)} succeeded")

    conn.close()


if __name__ == "__main__":
    main()
