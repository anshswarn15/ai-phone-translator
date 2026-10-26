# This defines a contract that every translation model must follow, allowing us to replace the model without rewriting the service.

from abc import ABC, abstractmethod

class TranslationProvider(ABC):

    """Common interface for translation model providers."""

    @abstractmethod

    async def translate(

        self,

        text: str,

        source_language: str,

        target_language: str,

    ) -> str:

        """Translate text from the source language into the target language."""

        raise NotImplementedError