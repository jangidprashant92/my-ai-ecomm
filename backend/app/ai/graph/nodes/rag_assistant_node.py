from typing import Any

from app.ai.graph.state import ChatState
from app.ai.rag.service import RagService


class RagAssistantNode:
    def __init__(
        self,
        rag_service: RagService,
    ) -> None:
        self.rag_service = rag_service

    async def run(
        self,
        state: ChatState,
    ) -> dict[str, Any]:

        messages = state["messages"]

        last_message = messages[-1]

        history = messages[:-1]

        answer, documents = await self.rag_service.answer(
            query=str(last_message.content),
            history=history,
        )

        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": answer,
                }
            ],
            "rag_sources": [
                {
                    "document_id": document.metadata.get("document_id"),
                    "source": document.metadata.get("source"),
                    "document_type": document.metadata.get("document_type"),
                    "category": document.metadata.get("category"),
                    "score": document.score,
                }
                for document in documents
            ],
        }


def create_rag_node(
    rag_service: RagService,
):
    node = RagAssistantNode(
        rag_service=rag_service,
    )

    async def rag_node(
        state: ChatState,
    ) -> dict[str, Any]:
        return await node.run(state)

    return rag_node
