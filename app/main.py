from fastapi import FastAPI

from app.api.routes.translation import router as translation_router
from app.api.routes.voice import router as voice_router


app = FastAPI(
    title="AI Phone Translator",
    description="Real-time English-Japanese translation.",
    version="0.1.0",
)

# Register the translation endpoint.
app.include_router(translation_router)

app.include_router(voice_router, prefix="/voice", tags=["Voice"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "AI Phone Translator API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}