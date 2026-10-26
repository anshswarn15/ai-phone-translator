from fastapi import APIRouter, HTTPException

from app.integrations.llm.nllb_translation_provider import (
    NLLBTranslationProvider,
)
from app.schemas.translation import (
    TranslationRequest,
    TranslationResponse,
)
from app.services.translation_service import TranslationService


router = APIRouter(prefix="/translation", tags=["Translation"])

# Reuse the provider and service instead of loading models for each request.
provider = NLLBTranslationProvider()
service = TranslationService(provider)


@router.post("/", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
) -> TranslationResponse:
    """Translate text between English and Japanese."""

    try:
        return await service.translate(request)
    except ValueError as exc:
        # Convert expected input errors into an HTTP 400 response.
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc