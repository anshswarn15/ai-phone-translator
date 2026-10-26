# This test downloads and loads a real model on its first run, so it is an integration test rather than a lightweight unit test.

import pytest

from app.integrations.llm.marian_translation_provider import (
    MarianTranslationProvider,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("text", "source_language", "target_language"),
    [
        ("Hello, how are you?", "en", "ja"),
        ("こんにちは、お元気ですか？", "ja", "en"),
    ],
)
async def test_real_translation(
    text: str,
    source_language: str,
    target_language: str,
) -> None:
    """Verify that the local model returns non-empty translated text."""

    provider = MarianTranslationProvider()

    translated_text = await provider.translate(
        text=text,
        source_language=source_language,
        target_language=target_language,
    )

    assert translated_text
    assert translated_text.strip() != text.strip()