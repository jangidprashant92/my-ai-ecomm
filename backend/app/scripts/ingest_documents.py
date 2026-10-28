from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.ai.rag.embeddings import EmbeddingProvider
from app.ai.rag.loaders import KnowledgeBaseLoader
from app.ai.rag.splitters import DocumentSplitter
from app.ai.rag.vector_store import QdrantKnowledgeStore
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

# Load the backend environment file without overwriting existing
# environment variables.
load_dotenv(ENV_FILE, override=False)


def resolve_knowledge_base_path() -> Path:
    """Resolve the shared corpus path for ingestion and BM25 retrieval."""

    configured_path = os.getenv("KNOWLEDGE_BASE_PATH", "").strip()

    if configured_path:
        path = Path(configured_path).expanduser()
        if not path.is_absolute():
            path = BACKEND_DIR / path
    else:
        path = BACKEND_DIR / "docs" / "documents"

    return path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index Markdown knowledge-base documents into Qdrant."
    )
    parser.add_argument(
        "--confirm-recreate",
        action="store_true",
        help=(
            "Confirm that the existing Qdrant collection may be replaced. "
            "Without this flag, indexing will not run."
        ),
    )
    args = parser.parse_args()

    if not args.confirm_recreate:
        parser.error(
            "Indexing recreates the Qdrant collection. "
            "Review the configured path and rerun with --confirm-recreate "
            "only when you intend to replace the existing index."
        )

    documents_path = resolve_knowledge_base_path()

    print(f"Backend directory: {BACKEND_DIR}")
    print(f"Knowledge-base directory: {documents_path}")

    if not documents_path.is_dir():
        raise FileNotFoundError(
            f"Knowledge-base directory does not exist: {documents_path}"
        )

    loader = KnowledgeBaseLoader(
        root_path=str(documents_path),
    )
    documents = loader.load()

    if not documents:
        raise ValueError(f"No Markdown documents were found in {documents_path}")

    print(f"Loaded {len(documents)} source documents.")

    # Keep these values aligned with build_bm25_retriever().
    chunk_size = 800
    chunk_overlap = 120

    splitter = DocumentSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split(documents)

    if not chunks:
        raise ValueError(
            "Document splitting produced no chunks. "
            "Check the knowledge-base files and splitter configuration."
        )

    print(
        f"Created {len(chunks)} chunks "
        f"(chunk_size={chunk_size}, "
        f"chunk_overlap={chunk_overlap})."
    )

    embedding_provider = EmbeddingProvider()

    vector_store = QdrantKnowledgeStore(
        embeddings=embedding_provider.embeddings,
    )

    print(
        "Replacing the configured Qdrant collection with the "
        "validated knowledge-base chunks..."
    )
    vector_store.recreate_from_documents(chunks)

    print("Documents successfully indexed in Qdrant.")


if __name__ == "__main__":
    main()
