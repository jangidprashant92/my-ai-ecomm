from app.core.config import settings
from langchain_openai import AzureOpenAIEmbeddings
from pydantic import SecretStr


class EmbeddingProvider:
    """Creates the embedding model used by the RAG pipeline."""

    def __init__(self) -> None:
        # self._embeddings = OllamaEmbeddings(
        #     model=settings.EMBEDDING_MODEL,
        # )

        self._embeddings = AzureOpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            azure_endpoint=settings.EMBEDDING_ENDPOINT,
            api_key=SecretStr(settings.OPENAI_API_KEY),
            dimensions=settings.EMBEDDING_DIMENSIONS,
            max_retries=3,
        )

    @property
    def embeddings(self):
        """Return the configured embedding model."""

        return self._embeddings
