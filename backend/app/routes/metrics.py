"""Read-only endpoints that expose the evaluation results to the frontend.

GET /metrics                 -> contents of outputs/metrics.json (written by evaluate.py)
GET /metrics/plot/{filename} -> a PNG from outputs/plots/ (confusion matrices, ROC, curves ...)

Nothing here runs a model or writes a file. If evaluate.py has not been run yet,
/metrics answers 404 with a message telling the user what to do.
"""
import json
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import OUTPUT_DIR, PLOTS_DIR

router = APIRouter(prefix="/metrics", tags=["metrics"])

OUTPUTS_DIR = OUTPUT_DIR.resolve()
_PLOTS = PLOTS_DIR.resolve()

# Only plain "name.png" files; no slashes, no "..", nothing hidden.
_PLOT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.png$")


def _load_metrics() -> dict:
    src = OUTPUTS_DIR / "metrics.json"
    if not src.is_file():
        raise HTTPException(
            status_code=404,
            detail="No evaluation results yet. Run `python evaluate.py` in the backend folder first.",
        )
    try:
        data = json.loads(src.read_text())
    except (OSError, ValueError):
        raise HTTPException(status_code=500, detail="outputs/metrics.json could not be read.")
    if not isinstance(data, dict) or not data:
        raise HTTPException(status_code=404, detail="outputs/metrics.json is empty. Run `python evaluate.py` again.")
    return data


@router.get("")
def get_metrics():
    raw = _load_metrics()
    models = []
    for name, r in raw.items():
        try:
            (tn, fp), (fn, tp) = r["confusion_matrix"]
            models.append({
                "name": name,
                "model": r.get("model", name),
                "loss": r.get("loss", ""),
                "accuracy": r["accuracy"],
                "precision": r["precision"],
                "recall": r["recall_sensitivity"],
                "specificity": r["specificity"],
                "f1": r["f1"],
                "roc_auc": r["roc_auc"],
                "tn": tn, "fp": fp, "fn": fn, "tp": tp,
                "ms_per_image": r.get("ms_per_image"),
                "parameters_millions": r.get("parameters_millions"),
                "file_size_mb": r.get("file_size_mb"),
            })
        except (KeyError, TypeError, ValueError):
            continue  # skip an entry that is not in the expected format
    if not models:
        raise HTTPException(status_code=500, detail="outputs/metrics.json has an unexpected format.")

    models.sort(key=lambda m: m["f1"], reverse=True)
    first = models[0]
    plots = sorted(p.name for p in _PLOTS.glob("*.png")) if _PLOTS.is_dir() else []
    return {
        "models": models,
        "test_size": first["tn"] + first["fp"] + first["fn"] + first["tp"],
        "plots": plots,
    }


@router.get("/plot/{filename}")
def get_plot(filename: str):
    if not _PLOT_NAME.match(filename):
        raise HTTPException(status_code=404, detail="Plot not found.")
    path = (_PLOTS / filename).resolve()
    if path.parent != _PLOTS or not path.is_file():
        raise HTTPException(status_code=404, detail="Plot not found.")
    return FileResponse(path, media_type="image/png")
