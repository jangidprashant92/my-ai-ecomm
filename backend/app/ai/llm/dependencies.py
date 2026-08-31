from app.ai.llm.base import (
    BaseLLMProvider,
)
from app.ai.llm.factory import (
    LLMFactory,
)


def get_llm_provider() -> BaseLLMProvider:

    return LLMFactory.create()
