from collections.abc import AsyncIterator

from app.ai.llm.base import BaseLLMProvider
from app.core.config import settings
from langchain_mistralai import ChatMistralAI
from pydantic import SecretStr


class MistralLLMProvider(BaseLLMProvider):
    def __init__(self):

        self.llm = ChatMistralAI(
            api_key=SecretStr(settings.MISTRAL_API_KEY),
            model_name=settings.MISTRAL_MODEL,
            temperature=0.7,
        )

    async def generate(
        self,
        messages: list,
        **kwargs,
    ) -> str:

        response = await self.llm.ainvoke(messages)

        return response.content

    async def stream(
        self,
        messages: list,
        **kwargs,
    ) -> AsyncIterator[str]:
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield str(chunk.content)
