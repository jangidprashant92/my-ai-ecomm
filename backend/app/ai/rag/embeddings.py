from app.core.config import settings
from langchain_ollama import OllamaEmbeddings


class EmbeddingProvider:
    """Creates the embedding model used by the RAG pipeline."""

    def __init__(self) -> None:
        self._embeddings = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL,
        )

    @property
    def embeddings(self) -> OllamaEmbeddings:
        """Return the configured embedding model."""

        return self._embeddings


# class EmbeddingProvider:
#     """Provides the Azure OpenAI embedding model."""

#     def __init__(self) -> None:
#         self._embeddings = AzureOpenAIEmbeddings(
#             model=settings.EMBEDDING_MODEL,
#             azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
#             azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
#             api_key=settings.AZURE_OPENAI_API_KEY,
#             openai_api_version=settings.AZURE_OPENAI_API_VERSION,
#             dimensions=settings.EMBEDDING_DIMENSIONS,
#             max_retries=3,
#         )

#     @property
#     def embeddings(self) -> AzureOpenAIEmbeddings:
#         """Return the configured embedding model."""

#         return self._embeddings
