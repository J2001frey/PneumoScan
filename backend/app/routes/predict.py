import io
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.claude_service import generate_explanation
from app.config import DISCLAIMER, MAX_UPLOAD_MB, MODEL_FILE
from app.model_registry import get_predictor
from app.schemas import PredictionResponse

router = APIRouter(tags=["prediction"])
ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png"}


def read_upload_image(file: UploadFile) -> Image.Image:
    """Validate an uploaded file and return it as a PIL image (shared by /predict and /predict/compare)."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Please upload a JPEG or PNG image.")

    limit = MAX_UPLOAD_MB * 1024 * 1024
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(413, f"Image is larger than {MAX_UPLOAD_MB} MB.")

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "Could not read the uploaded file as an image.")
    return image


# Plain `def` (not async) so FastAPI runs the blocking torch/Claude calls in a thread pool.
@router.post("/predict", response_model=PredictionResponse)
def predict(file: UploadFile = File(...), model_file: Optional[str] = Form(default=None)):
    """Full analysis (prediction + Grad-CAM + explanation).

    `model_file` is optional: a checkpoint name from GET /models. Without it the model from
    MODEL_FILE in .env is used, exactly as before.
    """
    image = read_upload_image(file)

    try:
        predictor = get_predictor(model_file)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError:
        raise HTTPException(503, f"Model file '{model_file or MODEL_FILE}' not found in saved_models/. Train a model first.")

    result = predictor.predict(image)
    explanation = generate_explanation(result)

    return PredictionResponse(
        label=result["label"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        low_confidence=result["low_confidence"],
        heatmap_base64=f"data:image/png;base64,{result['heatmap_base64']}",
        explanation=explanation,
        disclaimer=DISCLAIMER,
        model_name=result["model_name"],
    )
