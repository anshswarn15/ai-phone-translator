import asyncio

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from app.services.translation_provider import TranslationProvider


class NLLBTranslationProvider(TranslationProvider):
    MODEL_NAME = "facebook/nllb-200-distilled-600M"

    LANGUAGE_CODES = {
        "en": "eng_Latn",
        "ja": "jpn_Jpan",
    }

    def __init__(self):
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self._load_lock = asyncio.Lock()
        self._inference_lock = asyncio.Lock()

    async def _load_model(self):
        # Load the model only once, even if multiple requests arrive.
        async with self._load_lock:
            if self.model is None:
                self.tokenizer = await asyncio.to_thread(
                    AutoTokenizer.from_pretrained,
                    self.MODEL_NAME,
                )
                self.model = await asyncio.to_thread(
                    AutoModelForSeq2SeqLM.from_pretrained,
                    self.MODEL_NAME,
                )
                self.model.to(self.device)
                self.model.eval()

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        await self._load_model()

        async with self._inference_lock:
            return await asyncio.to_thread(
                self._translate_sync,
                text,
                source_language,
                target_language,
            )

    def _translate_sync(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        self.tokenizer.src_lang = self.LANGUAGE_CODES[source_language]

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self.device)

        with torch.inference_mode():
            output_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(
                    self.LANGUAGE_CODES[target_language]
                ),
                max_new_tokens=256,
                num_beams=4,
            )

        return self.tokenizer.batch_decode(
            output_tokens,
            skip_special_tokens=True,
        )[0]