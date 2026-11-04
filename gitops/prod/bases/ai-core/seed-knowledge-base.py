#!/usr/bin/env python3
"""
Dark NOC — RAG Knowledge Base Seeder
=====================================
PURPOSE:
    Seeds the pgvector database with NOC runbooks and past incident
    patterns. This gives the LangGraph agent domain-specific context
    when analyzing logs and generating remediation actions.

HOW IT WORKS:
    1. Reads all .md files from the runbooks/ directory
    2. Chunks each runbook into 512-token segments
    3. Embeds each chunk using sentence-transformers MiniLM-L6-v2
       (384-dimensional embeddings — compact and fast)
    4. Inserts chunks + embeddings into pgvector documents table
    5. Creates HNSW index for fast approximate nearest neighbor search

WHY MINILM-L6-V2:
    - 384 dimensions (vs 1536 for OpenAI ada-002) — 4x smaller index
    - 80ms per embedding on CPU — fast enough for seeding
    - Excellent retrieval quality for technical/operations text
    - Runs locally — no external API calls needed

USAGE:
    pip install psycopg2-binary sentence-transformers
    python seed-knowledge-base.py

    OR run as a Kubernetes Job:
    oc create job rag-seed --image=python:3.12 -- \
        python /scripts/seed-knowledge-base.py
"""

import os
import sys
import glob
import psycopg2
from sentence_transformers import SentenceTransformer

# Configuration from environment (or defaults for testing)
PG_HOST = os.getenv("PGVECTOR_HOST", "pgvector-postgres-rw.dark-noc-rag.svc")
PG_PORT = int(os.getenv("PGVECTOR_PORT", "5432"))
PG_DB = os.getenv("PGVECTOR_DB", "noc_rag")
PG_USER = os.getenv("PGVECTOR_USER", "noc_agent")
PG_PASSWORD = os.getenv("PGVECTOR_PASSWORD", "pgvector-noc-demo-2026")
RUNBOOKS_DIR = os.getenv("RUNBOOKS_DIR", "runbooks/")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return [c for c in chunks if len(c.strip()) > 50]  # Skip tiny chunks


def load_runbooks(directory: str) -> list[dict]:
    """Load all .md runbook files from directory."""
    runbooks = []
    pattern = os.path.join(directory, "*.md")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"WARNING: No .md files found in {directory}", file=sys.stderr)
        return []

    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract title from first H1 header
        title = filename.replace(".md", "").replace("-", " ").title()
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        runbooks.append({
            "filename": filename,
            "title": title,
            "content": content,
        })
        print(f"  Loaded: {filename} ({len(content)} chars)")

    return runbooks


def seed_database(runbooks: list[dict], model: SentenceTransformer) -> int:
    """Embed runbook chunks and insert into pgvector."""
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=PG_PASSWORD
    )

    total_inserted = 0
    try:
        with conn.cursor() as cur:
            # Clear existing runbook data (idempotent re-seeding)
            cur.execute("DELETE FROM documents WHERE metadata->>'type' = 'runbook'")
            deleted = cur.rowcount
            if deleted > 0:
                print(f"  Cleared {deleted} existing runbook chunks")

            for runbook in runbooks:
                chunks = chunk_text(runbook["content"], CHUNK_SIZE, CHUNK_OVERLAP)
                print(f"  Embedding {runbook['filename']}: {len(chunks)} chunks")

                for i, chunk in enumerate(chunks):
                    # Embed the chunk
                    embedding = model.encode(chunk).tolist()

                    # Build metadata
                    metadata = {
                        "type": "runbook",
                        "title": runbook["title"],
                        "filename": runbook["filename"],
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }

                    cur.execute(
                        """INSERT INTO documents (content, embedding, metadata)
                           VALUES (%s, %s::vector, %s)""",
                        (chunk, str(embedding), psycopg2.extras.Json(metadata))
                    )
                    total_inserted += 1

            conn.commit()
            print(f"\n✅ Inserted {total_inserted} chunks total")

            # Verify HNSW index exists
            cur.execute("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'documents'
                  AND indexdef LIKE '%hnsw%'
            """)
            idx = cur.fetchone()
            if idx:
                print(f"✅ HNSW index active: {idx[0]}")
            else:
                print("⚠️  HNSW index not found — creating...")
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS documents_embedding_hnsw
                    ON documents USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """)
                conn.commit()
                print("✅ HNSW index created")

    finally:
        conn.close()

    return total_inserted


def test_retrieval(model: SentenceTransformer) -> None:
    """Test a sample RAG query to confirm seeding worked."""
    test_query = "nginx pod OOMKilled out of memory remediation"
    print(f"\n🔍 Test query: '{test_query}'")

    query_embedding = model.encode(test_query).tolist()

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=PG_PASSWORD
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT content, metadata->>'title' as title,
                          1 - (embedding <=> %s::vector) as similarity
                   FROM documents
                   ORDER BY embedding <=> %s::vector
                   LIMIT 3""",
                (str(query_embedding), str(query_embedding))
            )
            results = cur.fetchall()

            print(f"\nTop 3 results:")
            for i, (content, title, similarity) in enumerate(results, 1):
                print(f"  {i}. [{similarity:.3f}] {title}")
                print(f"     {content[:100]}...")

    finally:
        conn.close()


def main():
    print("=" * 60)
    print(" Dark NOC — RAG Knowledge Base Seeder")
    print("=" * 60)

    # Load runbooks
    print(f"\n📂 Loading runbooks from {RUNBOOKS_DIR}...")
    runbooks = load_runbooks(RUNBOOKS_DIR)
    if not runbooks:
        print("ERROR: No runbooks found. Check RUNBOOKS_DIR.", file=sys.stderr)
        sys.exit(1)
    print(f"  Loaded {len(runbooks)} runbooks")

    # Load embedding model
    print(f"\n🤖 Loading embedding model: {EMBED_MODEL}")
    print("  (Downloads ~90MB on first run — cached after)")
    model = SentenceTransformer(EMBED_MODEL)
    print(f"  Model loaded. Embedding dim: {model.get_sentence_embedding_dimension()}")

    # Seed database
    print(f"\n💾 Seeding pgvector database at {PG_HOST}:{PG_PORT}/{PG_DB}...")
    total = seed_database(runbooks, model)

    # Test retrieval
    test_retrieval(model)

    print(f"\n{'=' * 60}")
    print(f" ✅ RAG seeding complete: {total} chunks stored")
    print(f"    Database: {PG_HOST}:{PG_PORT}/{PG_DB}")
    print(f"    Query with: SELECT * FROM documents ORDER BY embedding <=> $1 LIMIT 5")
    print("=" * 60)


if __name__ == "__main__":
    import psycopg2.extras
    main()
