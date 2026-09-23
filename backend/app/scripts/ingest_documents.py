from app.ai.rag.embeddings import EmbeddingProvider
from app.ai.rag.loaders import KnowledgeBaseLoader
from app.ai.rag.splitters import DocumentSplitter
from app.ai.rag.vector_store import QdrantKnowledgeStore


def main() -> None:
    documents_path = "docs/documents"

    print(f"Loading documents from: {documents_path}")

    loader = KnowledgeBaseLoader(documents_path)
    documents = loader.load()

    print(f"Loaded {len(documents)} documents.")

    splitter = DocumentSplitter()
    chunks = splitter.split(documents)

    print(f"Created {len(chunks)} chunks.")

    embedding_provider = EmbeddingProvider()
    embeddings = embedding_provider.embeddings

    vector_store = QdrantKnowledgeStore(
        embeddings=embeddings,
    )

    vector_store.recreate_from_documents(chunks)

    print("Documents successfully indexed in Qdrant.")


if __name__ == "__main__":
    main()
