from dataclasses import dataclass

from app.ai.rag.vector_store import QdrantKnowledgeStore
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

RAG_SYSTEM_PROMPT = """
You are CommerceOps AI.

Answer the user's question using only the provided
knowledge-base context.

Rules:
- Do not invent information.
- Do not use knowledge outside the provided context.
- If the context does not contain the answer, say that
  the knowledge base does not contain enough information.
- Keep the answer clear and concise.
- Do not claim that a business action was performed.
"""


@dataclass(slots=True)
class RetrievedDocument:
    """Retrieved document with its similarity score."""

    content: str
    metadata: dict
    score: float


class RagService:
    """Standalone retrieval-augmented generation service."""

    def __init__(
        self,
        vector_store: QdrantKnowledgeStore,
        model: BaseChatModel,
    ) -> None:
        self.vector_store = vector_store
        self.model = model

    def retrieve(
        self,
        query: str,
        k: int = 4,
    ) -> list[RetrievedDocument]:
        results = self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
        )

        return [
            RetrievedDocument(
                content=document.page_content,
                metadata=document.metadata,
                score=float(score),
            )
            for document, score in results
        ]

    async def answer(
        self,
        query: str,
        k: int = 4,
    ) -> tuple[str, list[RetrievedDocument]]:

        documents = self.retrieve(
            query=query,
            k=k,
        )

        if not documents:
            return (
                "I could not find relevant information in the knowledge base.",
                [],
            )

        context = "\n\n---\n\n".join(
            (f"Source: {doc.metadata.get('source')}\n{doc.content}")
            for doc in documents
        )

        response = await self.model.ainvoke(
            [
                SystemMessage(
                    content=RAG_SYSTEM_PROMPT,
                ),
                HumanMessage(
                    content=(
                        f"Question:\n{query}\n\nKnowledge Base Context:\n{context}"
                    ),
                ),
            ],
        )

        return (
            str(response.content),
            documents,
        )
