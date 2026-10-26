# Now let’s test the translation schemas for English ↔ Japanese before implementing the actual translation model.

import pytest
from pydantic import ValidationError

from app.schemas.translation import TranslationRequest


def test_english_to_japanese_request() -> None:
    """Accept a valid English-to-Japanese request."""
    request = TranslationRequest(
        text="Hello, how are you?",
        source_language="en",
        target_language="ja",
    )

    assert request.source_language == "en"
    assert request.target_language == "ja"


def test_japanese_to_english_request() -> None:
    """Accept a valid Japanese-to-English request."""
    request = TranslationRequest(
        text="こんにちは",
        source_language="ja",
        target_language="en",
    )

    assert request.source_language == "ja"
    assert request.target_language == "en"


def test_reject_identical_languages() -> None:
    """Reject requests where source and target languages are identical."""
    with pytest.raises(
        ValidationError,
        match="Source and target languages must be different",
    ):
        TranslationRequest(
            text="Hello",
            source_language="en",
            target_language="en",
        )


def test_reject_unsupported_language() -> None:
    """Reject languages that are not currently supported."""
    with pytest.raises(ValidationError):
        TranslationRequest(
            text="Hello",
            source_language="fr",
            target_language="ja",
        )


def test_reject_empty_text() -> None:
    """Reject empty translation input."""
    with pytest.raises(ValidationError):
        TranslationRequest(
            text="",
            source_language="en",
            target_language="ja",
        )