"""Central configuration.

All paths are resolved relative to this file, so the code finds the local
dataset no matter which directory you launch it from.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
load_dotenv(BASE_DIR / ".env")

# ---- Paths (dataset is read directly from disk, never uploaded) ----
DATA_DIR = BASE_DIR / "data" / "chest_xray"
MODEL_DIR = BASE_DIR / "saved_models"
OUTPUT_DIR = BASE_DIR / "outputs"
PLOTS_DIR = OUTPUT_DIR / "plots"
GRADCAM_DIR = OUTPUT_DIR / "gradcam_samples"
for _d in (MODEL_DIR, PLOTS_DIR, GRADCAM_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---- Data / training ----
CLASS_NAMES = ["NORMAL", "PNEUMONIA"]  # ImageFolder sorts alphabetically
POSITIVE_CLASS = 1                     # PNEUMONIA is the "positive" class
IMG_SIZE = 224
BATCH_SIZE = 32
SEED = 42
VAL_FRACTION = 0.15
NUM_WORKERS = 0 if os.name == "nt" else 2

# ---- API / inference ----
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:4200")
MODEL_FILE = os.getenv("MODEL_FILE", "mobilenetv2_weighted_ce.pt")
LOW_CONFIDENCE_THRESHOLD = 0.75
MAX_UPLOAD_MB = 10
DISCLAIMER = "Screening aid only. Not a medical diagnosis. Consult a qualified clinician."


def get_device():
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
