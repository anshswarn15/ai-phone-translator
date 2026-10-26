# This coordinates translation requests without depending on a particular model.

from app.schemas.translation import (
    TranslationRequest,
    TranslationResponse,
)
from app.services.translation_provider import TranslationProvider


class TranslationService:
    """Coordinate translation requests independently of the model."""

    def __init__(self, provider: TranslationProvider) -> None:
        # Inject the provider instead of creating it inside the service.
        self._provider = provider

    async def translate(
        self,
        request: TranslationRequest,
    ) -> TranslationResponse:
        """Translate validated input and return structured output."""

        # Delegate translation to the configured provider.
        translated_text = await self._provider.translate(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
        )

        # Return the translation with its language and provider metadata.
        return TranslationResponse(
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language,
            model=type(self._provider).__name__,
        )