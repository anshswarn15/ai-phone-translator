import asyncio
from functools import partial

import torch
from transformers import MarianMTModel, MarianTokenizer

from app.services.translation_provider import TranslationProvider


class MarianTranslationProvider(TranslationProvider):
    """Translate text between English and Japanese using MarianMT."""

    # Use a dedicated model for each translation direction.
    MODEL_NAMES = {
        ("en", "ja"): "Helsinki-NLP/opus-mt-en-jap",
        ("ja", "en"): "Helsinki-NLP/opus-mt-jap-en",
    }

    def __init__(self) -> None:
        # Prefer Apple's Metal GPU when supported; otherwise use the CPU.
        self._device = torch.device(
            "mps" if torch.backends.mps.is_available() else "cpu"
        )

        # Cache each model and tokenizer to avoid reloading them per request.
        self._models: dict[
            tuple[str, str],
            tuple[MarianTokenizer, MarianMTModel],
        ] = {}

        # Protect model loading and inference from concurrent access.
        self._initialization_lock = asyncio.Lock()
        self._inference_lock = asyncio.Lock()

    async def _load_model(
        self,
        source_language: str,
        target_language: str,
    ) -> tuple[MarianTokenizer, MarianMTModel]:
        """Load a translation model once and reuse it."""

        language_pair = (source_language, target_language)

        # Return the cached model if this language direction is already loaded.
        if language_pair in self._models:
            return self._models[language_pair]

        async with self._initialization_lock:
            # Check again because another request may have loaded it while waiting.
            if language_pair in self._models:
                return self._models[language_pair]

            model_name = self.MODEL_NAMES.get(language_pair)

            if model_name is None:
                raise ValueError(
                    f"Unsupported language pair: {source_language} "
                    f"to {target_language}"
                )

            # Loading models is blocking, so run it in a worker thread.
            tokenizer, model = await asyncio.to_thread(
                self._load_model_sync,
                model_name,
            )

            self._models[language_pair] = (tokenizer, model)

        return self._models[language_pair]

    def _load_model_sync(
        self,
        model_name: str,
    ) -> tuple[MarianTokenizer, MarianMTModel]:
        """Load the tokenizer and model synchronously."""

        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)

        # Move the model to the selected device and disable training behavior.
        model.to(self._device)
        model.eval()

        return tokenizer, model

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Translate text without blocking the asynchronous event loop."""

        tokenizer, model = await self._load_model(
            source_language,
            target_language,
        )

        # Serialize inference to avoid competing executions on the same device.
        async with self._inference_lock:
            translated_text = await asyncio.to_thread(
                partial(
                    self._translate_sync,
                    text,
                    tokenizer,
                    model,
                )
            )

        return translated_text

    def _translate_sync(
        self,
        text: str,
        tokenizer: MarianTokenizer,
        model: MarianMTModel,
    ) -> str:
        """Tokenize input, generate a translation, and decode the output."""

        # Convert the input sentence into tensors and limit its token length.
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        # Ensure the input tensors and model use the same device.
        inputs = {
            name: tensor.to(self._device)
            for name, tensor in inputs.items()
        }

        # Beam search considers multiple candidate translations.
        with torch.inference_mode():
            output_tokens = model.generate(
                **inputs,
                max_new_tokens=256,
                num_beams=4,
                early_stopping=True,
            )

        # Convert generated tokens into readable text.
        translated_text = tokenizer.decode(
            output_tokens[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        ).strip()

        if not translated_text:
            raise RuntimeError(
                "The translation model returned empty output."
            )

        return translated_text