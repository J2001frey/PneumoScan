"""Model switcher endpoints.

GET  /models           -> the trained models available in saved_models/ (with test metrics when known)
POST /predict/compare  -> run EVERY available model on one image and return their predictions side by side
                          (prediction only: no Grad-CAM and no Claude call, so it is fast and free)
"""
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.model_registry import get_predictor, list_models
from app.routes.predict import read_upload_image

router = APIRouter(tags=["models"])


class ModelInfo(BaseModel):
    file: str
    name: str
    architecture: str
    label: str
    is_default: bool
    test_f1: Optional[float] = None
    test_recall: Optional[float] = None
    test_roc_auc: Optional[float] = None


class ModelListResponse(BaseModel):
    default: str
    models: List[ModelInfo]


class CompareItem(BaseModel):
    file: str
    name: str
    label: str
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    low_confidence: Optional[bool] = None
    ms: Optional[float] = None
    error: Optional[str] = None


class CompareResponse(BaseModel):
    results: List[CompareItem]


@router.get("/models", response_model=ModelListResponse)
def models():
    return list_models()


@router.post("/predict/compare", response_model=CompareResponse)
def compare(file: UploadFile = File(...)):
    image = read_upload_image(file)

    available = list_models()["models"]
    if not available:
        raise HTTPException(503, "No trained models found in saved_models/. Train a model first.")

    results = []
    for m in available:
        item = {"file": m["file"], "name": m["name"], "label": m["label"]}
        try:
            predictor = get_predictor(m["file"])
            t0 = time.perf_counter()
            r = predictor.predict_quick(image)
            item.update(
                prediction=r["label"],
                confidence=r["confidence"],
                probabilities=r["probabilities"],
                low_confidence=r["low_confidence"],
                ms=round((time.perf_counter() - t0) * 1000, 1),
            )
        except Exception as e:  # a single broken checkpoint must not hide the other models
            item["error"] = f"Could not run this model ({type(e).__name__})."
        results.append(item)

    return {"results": results}
