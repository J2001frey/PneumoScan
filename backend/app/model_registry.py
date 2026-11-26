"""Which trained models exist in saved_models/, and a cache of loaded predictors.

Every checkpoint found in saved_models/ (e.g. mobilenetv2_weighted_ce.pt, resnet50_weighted_ce.pt,
custom_cnn_weighted_ce.pt) can be served, so the frontend can switch between models or compare them
on the same image. The model named by MODEL_FILE in .env stays the default.
"""
import json
import threading
from typing import Optional

from app.config import MODEL_DIR, MODEL_FILE, OUTPUT_DIR
from app.models import MODEL_NAMES
from app.predictor import Predictor

_LABELS = {"mobilenetv2": "MobileNetV2", "resnet50": "ResNet50", "custom_cnn": "Custom CNN"}

_cache: dict = {}
_lock = threading.Lock()


def available_model_files() -> list:
    if not MODEL_DIR.is_dir():
        return []
    return sorted(p.name for p in MODEL_DIR.glob("*.pt"))


def resolve_model_file(requested: Optional[str]) -> str:
    """Return the checkpoint file name to use. Only files that really exist in saved_models/ are accepted,
    so a request can never point at an arbitrary path."""
    if not requested:
        return MODEL_FILE
    if requested not in available_model_files():
        raise ValueError(f"Unknown model '{requested}'. Available: {', '.join(available_model_files()) or 'none'}.")
    return requested


def get_predictor(model_file: Optional[str] = None) -> Predictor:
    """Load a checkpoint once and keep it in memory (the three models together are about 105 MB)."""
    name = resolve_model_file(model_file)
    path = MODEL_DIR / name
    if not path.is_file():
        raise FileNotFoundError(path)
    with _lock:
        if name not in _cache:
            _cache[name] = Predictor(path)
        return _cache[name]


def _architecture(stem: str) -> Optional[str]:
    for n in MODEL_NAMES:
        if stem == n or stem.startswith(n + "_"):
            return n
    return None


def _test_metrics() -> dict:
    """Test-set numbers written by evaluate.py (optional; shown next to each model in the picker)."""
    try:
        data = json.loads((OUTPUT_DIR / "metrics.json").read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def list_models() -> dict:
    metrics = _test_metrics()
    items = []
    for f in available_model_files():
        stem = f[: -len(".pt")]
        arch = _architecture(stem)
        m = metrics.get(stem) if isinstance(metrics.get(stem), dict) else {}
        items.append({
            "file": f,
            "name": stem,
            "architecture": arch or stem,
            "label": _LABELS.get(arch, stem),
            "is_default": f == MODEL_FILE,
            "test_f1": m.get("f1"),
            "test_recall": m.get("recall_sensitivity"),
            "test_roc_auc": m.get("roc_auc"),
        })
    # best test F1 first; models without metrics go last
    items.sort(key=lambda i: (i["test_f1"] is None, -(i["test_f1"] or 0), i["file"]))
    return {"default": MODEL_FILE, "models": items}
