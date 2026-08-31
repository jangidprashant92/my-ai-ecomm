from collections.abc import AsyncGenerator

from app.core.config import settings
from langchain_mistralai.chat_models import ChatMistralAI


class LLMService:
    def __init__(self):
        print("Initializing LLMService...")
        print(f"MISTRAL_API_KEY: {settings.MISTRAL_API_KEY}")
        self.llm = ChatMistralAI(
            api_key=settings.MISTRAL_API_KEY,
            model_name="mistral-small-latest",
            temperature=0.7,
        )

    async def chat(self, messages):

        response = await self.llm.ainvoke(messages)
        return response.content

    async def stream_chat(self, messages) -> AsyncGenerator[str, None]:
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
