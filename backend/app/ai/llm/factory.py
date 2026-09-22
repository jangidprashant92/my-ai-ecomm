from app.core.config import settings
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


class LLMFactory:
    @staticmethod
    def create() -> BaseChatModel:
        return init_chat_model(
            settings.MODEL_NAME, max_tokens=1000, temperature=0.2, max_retries=2
        )

        # if provider == "mistral":
        #     return ChatMistralAI(
        #         api_key=SecretStr(settings.MISTRAL_API_KEY),
        #         model_name=settings.MISTRAL_MODEL,
        #         temperature=0,
        #         max_retries=2,
        #     )

        # if provider == "ollama":
        #     from langchain_ollama import ChatOllama

        #     return ChatOllama(
        #         model=settings.MODEL_NAME,
        #         temperature=0,
        #     )

        # raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
