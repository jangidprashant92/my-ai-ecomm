from app.ai.llm.base import (
    BaseLLMProvider,
)
from app.ai.llm.providers.mistral import (
    MistralLLMProvider,
)
from app.core.config import settings


class LLMFactory:
    @staticmethod
    def create() -> BaseLLMProvider:

        provider = (settings.LLM_PROVIDER).lower()

        if provider == "mistral":
            return MistralLLMProvider()

        # if provider == "openai":
        #     return OpenAILLMProvider()

        if provider == "ollama":
            from app.ai.llm.providers.ollama import OllamaProvider

            return OllamaProvider()

        raise ValueError(f"Unsupported LLM provider: {provider}")
