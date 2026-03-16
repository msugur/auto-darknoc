#!/usr/bin/env python3
"""
Dark NOC — Product Documentation Seeder for RAG

Fetches official documentation pages (Red Hat + supporting tools),
extracts readable text, embeds chunks, and stores them in pgvector.
"""

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any

import psycopg2
import psycopg2.extras
import requests
import yaml
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

PG_HOST = os.getenv("PGVECTOR_HOST", "pgvector-postgres-rw.dark-noc-rag.svc")
PG_PORT = int(os.getenv("PGVECTOR_PORT", "5432"))
PG_DB = os.getenv("PGVECTOR_DB", "noc_rag")
PG_USER = os.getenv("PGVECTOR_USER", "noc_agent")
PG_PASSWORD = os.getenv("PGVECTOR_PASSWORD", "pgvector-noc-demo-2026")

SOURCES_FILE = os.getenv("DOC_SOURCES_FILE", "/config/documentation-sources.yaml")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("DOC_CHUNK_SIZE", "1600"))
CHUNK_OVERLAP = int(os.getenv("DOC_CHUNK_OVERLAP", "200"))
MAX_PAGE_CHARS = int(os.getenv("MAX_PAGE_CHARS", "120000"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "40"))
USER_AGENT = "dark-noc-rag-doc-ingestor/1.0"


@dataclass
class DocPage:
    product: str
    version: str
    vendor: str
    category: str
    url: str
    title: str
    text: str


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) >= 200:
            chunks.append(chunk)
        if end == len(text):
            break
        start += max(1, size - overlap)
    return chunks


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = text.replace("\u00a0", " ")
    return text.strip()


def extract_html_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "header", "footer"]):
        tag.decompose()

    title = "Untitled"
    if soup.title and soup.title.string:
        title = normalize_text(soup.title.string)

    main_node = soup.find("main") or soup.find("article") or soup.body or soup
    text = normalize_text(main_node.get_text(" ", strip=True))
    return title, text[:MAX_PAGE_CHARS]


def load_sources(path: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "sources" not in data:
        raise ValueError("Invalid documentation sources file")

    version_pins = data.get("version_pins", {})
    sources = data["sources"]
    if not isinstance(sources, list):
        raise ValueError("'sources' must be a list")

    return version_pins, sources


def fetch_pages(sources: list[dict[str, Any]]) -> list[DocPage]:
    pages: list[DocPage] = []
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    for src in sources:
        product = src.get("product", "unknown")
        version = src.get("version", "unknown")
        vendor = src.get("vendor", "unknown")
        category = src.get("category", "general")
        urls = src.get("urls", [])

        for url in urls:
            try:
                print(f"Fetching: {url}")
                response = session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                title, text = extract_html_text(response.text)
                if len(text) < 500:
                    print(f"  Skipped (too little content): {url}")
                    continue

                pages.append(
                    DocPage(
                        product=product,
                        version=version,
                        vendor=vendor,
                        category=category,
                        url=url,
                        title=title,
                        text=text,
                    )
                )
                print(f"  OK: {title} ({len(text)} chars)")
            except Exception as exc:
                print(f"  ERROR: {url} -> {exc}", file=sys.stderr)

    return pages


def seed_docs(pages: list[DocPage], model: SentenceTransformer, version_pins: dict[str, Any]) -> int:
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )

    inserted = 0
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE metadata->>'type' = 'documentation'")
            deleted = cur.rowcount
            if deleted > 0:
                print(f"Cleared {deleted} prior documentation chunks")

            for page in pages:
                chunks = chunk_text(page.text, CHUNK_SIZE, CHUNK_OVERLAP)
                print(f"Embedding {page.product} {page.version}: {len(chunks)} chunks")

                for i, chunk in enumerate(chunks):
                    vec = model.encode(chunk).tolist()
                    metadata = {
                        "type": "documentation",
                        "doc_title": page.title,
                        "product": page.product,
                        "version": page.version,
                        "vendor": page.vendor,
                        "category": page.category,
                        "source_url": page.url,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "version_pins": version_pins,
                    }

                    cur.execute(
                        """
                        INSERT INTO documents (content, embedding, metadata)
                        VALUES (%s, %s::vector, %s)
                        """,
                        (chunk, str(vec), psycopg2.extras.Json(metadata)),
                    )
                    inserted += 1

            conn.commit()

            try:
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS documents_embedding_hnsw
                    ON documents USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                    """
                )
                conn.commit()
            except psycopg2.errors.InsufficientPrivilege:
                conn.rollback()
                print(
                    "WARN: skipping index creation (insufficient privilege). "
                    "Existing index will be reused if present."
                )

    finally:
        conn.close()

    return inserted


def main() -> int:
    print("=" * 68)
    print("Dark NOC — Product Documentation Seeder")
    print("=" * 68)

    version_pins, sources = load_sources(SOURCES_FILE)
    print(f"Loaded {len(sources)} documentation source groups")

    pages = fetch_pages(sources)
    if not pages:
        print("No documentation pages could be fetched.", file=sys.stderr)
        return 1

    print(f"Fetched {len(pages)} pages; loading embedding model {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    dim = model.get_sentence_embedding_dimension()
    print(f"Embedding model ready (dim={dim})")

    inserted = seed_docs(pages, model, version_pins)
    print(f"Inserted documentation chunks: {inserted}")

    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT metadata->>'product', COUNT(*)
                FROM documents
                WHERE metadata->>'type' = 'documentation'
                GROUP BY 1
                ORDER BY 1
                """
            )
            rows = cur.fetchall()
            print("Documentation chunk counts by product:")
            for product, count in rows:
                print(f"  - {product}: {count}")
    finally:
        conn.close()

    print("Documentation ingestion complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
