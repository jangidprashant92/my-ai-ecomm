from collections.abc import AsyncIterator

from app.ai.llm.base import BaseLLMProvider
from app.core.config import settings
from langchain_ollama import ChatOllama


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider implementation."""

    def __init__(self):

        self.llm = ChatOllama(
            model=settings.MODEL_NAME,
            reasoning=True,
            temperature=0.7,
        )

    async def generate(
        self,
        messages: list,
        **kwargs,
    ) -> str:

        response = await self.llm.ainvoke(messages)

        return response.content  # type: ignore

    async def stream(
        self,
        messages: list,
        **kwargs,
    ) -> AsyncIterator[dict[str, str]]:
        """
        Streams chunks distinguishing between thinking process and final text answer.
        Yields: {"type": "thinking" | "text", "content": str}
        """
        async for chunk in self.llm.astream(messages):
            # 1. Extract reasoning/thinking tokens
            reasoning_chunk = chunk.additional_kwargs.get("reasoning_content")
            if reasoning_chunk:
                yield {"type": "thinking", "content": str(reasoning_chunk)}

            # 2. Extract standard answer tokens
            if chunk.content:
                yield {"type": "text", "content": str(chunk.content)}
