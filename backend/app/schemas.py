from pydantic import BaseModel


class PredictionResponse(BaseModel):
    label: str
    confidence: float
    probabilities: dict[str, float]
    low_confidence: bool
    heatmap_base64: str  # data URI, ready for <img [src]>
    explanation: str
    disclaimer: str
    model_name: str


class HealthResponse(BaseModel):
    status: str
    model_file: str
    model_available: bool
    claude_configured: bool
