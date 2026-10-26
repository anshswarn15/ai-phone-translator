import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


# NLLB-200 distilled model for multilingual translation.
MODEL_NAME = "facebook/nllb-200-distilled-600M"

# NLLB uses language tags rather than the "en" and "ja" codes directly.
LANGUAGES = {
    "en": "eng_Latn",
    "ja": "jpn_Jpan",
}

# Prefer Apple Silicon GPU acceleration when available.
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"


def main() -> None:
    """Compare English-to-Japanese translation on representative sentences."""

    print(f"Loading {MODEL_NAME} on {DEVICE}...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(DEVICE)
    model.eval()

    test_sentences = [
        "Hello.",
        "Thank you.",
        "Good morning.",
        "Hello. Thank you for your help.",
        "How are you?",
    ]

    for sentence in test_sentences:
        # Tell the tokenizer which language the input text uses.
        tokenizer.src_lang = LANGUAGES["en"]

        inputs = tokenizer(
            sentence,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(DEVICE)

        # Force generation in Japanese instead of the model's default language.
        with torch.inference_mode():
            output_tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(
                    LANGUAGES["ja"]
                ),
                max_new_tokens=128,
                num_beams=4,
            )

        translation = tokenizer.batch_decode(
            output_tokens,
            skip_special_tokens=True,
        )[0]

        print(f"\nEnglish:  {sentence}")
        print(f"Japanese: {translation}")


if __name__ == "__main__":
    main()