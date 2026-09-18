from app.core.config import settings
from langchain_core.language_models import BaseChatModel
from langchain_mistralai import ChatMistralAI
from pydantic import SecretStr


class LLMFactory:
    @staticmethod
    def create() -> BaseChatModel:
        provider = settings.LLM_PROVIDER.lower()

        if provider == "mistral":
            return ChatMistralAI(
                api_key=SecretStr(settings.MISTRAL_API_KEY),
                model_name=settings.MISTRAL_MODEL,
                temperature=0,
                max_retries=2,
            )

        if provider == "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=settings.MODEL_NAME,
                temperature=0,
            )

        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
