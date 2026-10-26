from fastapi import APIRouter, Response
from twilio.twiml.voice_response import VoiceResponse

router = APIRouter()


@router.post("/incoming")
async def incoming_call():
    response = VoiceResponse()
    response.say(
        "Welcome to the AI Phone Translator. Please speak after the beep.",
        language="en-US",
    )

    # Ask Twilio to recognize the caller's English speech.
    gather = response.gather(
        input="speech",
        action="https://credible-impart-salute.ngrok-free.dev/voice/translate?source=en",
        method="POST",
        language="en-US",
        speech_timeout="auto",
    )
    gather.say("I am listening.", language="en-US")

    response.say("I did not receive any speech. Goodbye.", language="en-US")

    return Response(
        content=str(response),
        media_type="application/xml",
    )


from fastapi import Form, HTTPException, Response
from twilio.twiml.voice_response import VoiceResponse

from app.integrations.llm.nllb_translation_provider import (
    NLLBTranslationProvider,
)

# Reuse one model provider instead of loading the model for every request.
translation_provider = NLLBTranslationProvider()


@router.post("/translate")
async def translate_speech(
    SpeechResult: str = Form(...),
    source: str = "en",
):
    target = "ja" if source == "en" else "en"

    try:
        translated_text = await translation_provider.translate(
            text=SpeechResult,
            source_language=source,
            target_language=target,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Translation failed",
        ) from exc

    response = VoiceResponse()
    response.say(
        translated_text,
        language="ja-JP" if target == "ja" else "en-US",
    )

    return Response(
        content=str(response),
        media_type="application/xml",
    )