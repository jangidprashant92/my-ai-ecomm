# 10 — RAG Ingestion and Qdrant

Business knowledge source:

```text
backend/docs/documents/
```

These Markdown files are the RAG corpus. Engineering docs should remain under the top-level `docs/`.

## Loader

`KnowledgeBaseLoader` recursively loads Markdown and adds:

- `document_id`
- `source`
- `document_type`
- `category`

## Splitter

`DocumentSplitter` uses `RecursiveCharacterTextSplitter`.

Current defaults:

```text
chunk_size = 800
chunk_overlap = 120
```

## Embeddings

`EmbeddingProvider` currently uses Azure OpenAI embeddings.

## Ingestion

Script:

```text
backend/app/scripts/ingest_documents.py
```

Flow:

```text
Markdown
 ↓
Loader
 ↓
Documents
 ↓
Splitter
 ↓
Chunks
 ↓
Embeddings
 ↓
Qdrant
```

Run:

```bash
cd backend
uv run python -m app.scripts.ingest_documents
```

The current script recreates the configured Qdrant collection.

After changing source documents, chunking, or embedding configuration, rerun ingestion.

Useful probes:

```bash
uv run python -m app.scripts.test_embeddings
uv run python -m app.scripts.test_retrieval
uv run python -m app.scripts.test_rag
```
