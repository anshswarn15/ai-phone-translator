from typing import Literal

from pydantic import BaseModel, Field, model_validator


# Define the language codes supported by the application.
# "en" = English, "ja" = Japanese.
LanguageCode = Literal["en", "ja"]


class TranslationRequest(BaseModel):
    """Validate an incoming translation request."""

    # Reject empty input and limit text size to 5,000 characters.
    text: str = Field(min_length=1, max_length=5000)

    # Language of the original text.
    source_language: LanguageCode

    # Language required for the translated output.
    target_language: LanguageCode

    @model_validator(mode="after")
    def validate_languages(self) -> "TranslationRequest":
        # Reject requests that translate a language into itself.
        if self.source_language == self.target_language:
            raise ValueError(
                "Source and target languages must be different."
            )

        return self


class TranslationResponse(BaseModel):
    """Represent the result returned by the translation service."""

    # Text produced by the translation provider.
    translated_text: str = Field(min_length=1)

    # Language of the original text.
    source_language: LanguageCode

    # Language of the translated text.
    target_language: LanguageCode

    # Name of the provider that generated the translation.
    model: str = Field(min_length=1)