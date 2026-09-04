from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list,
        **kwargs,
    ) -> str:
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list,
        **kwargs,
    ) -> AsyncIterator[dict[str, str]]:
        if False:
            yield ""
