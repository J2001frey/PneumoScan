from fastapi import APIRouter

from app.config import ANTHROPIC_API_KEY, MODEL_DIR, MODEL_FILE
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        model_file=MODEL_FILE,
        model_available=(MODEL_DIR / MODEL_FILE).exists(),
        claude_configured=bool(ANTHROPIC_API_KEY),
    )
