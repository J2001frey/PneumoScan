"""Loads a trained model once and runs prediction + Grad-CAM on single images."""
import threading
from pathlib import Path

import torch
from PIL import Image

from app.config import CLASS_NAMES, LOW_CONFIDENCE_THRESHOLD, get_device
from app.dataset import eval_transform
from app.gradcam import GradCAM, overlay_heatmap, pil_to_base64
from app.models import build_model, get_target_layer


class Predictor:
    def __init__(self, model_path: Path):
        self.device = get_device()
        ckpt = torch.load(model_path, map_location=self.device)
        self.model_name = ckpt["model_name"]
        self.checkpoint_name = Path(model_path).stem
        self.model = build_model(self.model_name, pretrained=False)
        self.model.load_state_dict(ckpt["state"])
        self.model.to(self.device).eval()
        self.target_layer = get_target_layer(self.model, self.model_name)
        self._lock = threading.Lock()  # hooks are attached to a shared model

    def predict(self, pil_image: Image.Image) -> dict:
        img = pil_image.convert("RGB")
        x = eval_transform(img).unsqueeze(0).to(self.device)

        with self._lock:
            cam_engine = GradCAM(self.model, self.target_layer)
            try:
                cam, idx, probs = cam_engine(x)
            finally:
                cam_engine.remove()

        overlay = overlay_heatmap(img, cam)
        confidence = float(probs[idx])
        return {
            "label": CLASS_NAMES[idx],
            "confidence": confidence,
            "probabilities": {CLASS_NAMES[i]: float(p) for i, p in enumerate(probs)},
            "low_confidence": confidence < LOW_CONFIDENCE_THRESHOLD,
            "heatmap_base64": pil_to_base64(overlay),
            "model_name": self.checkpoint_name,
        }

    def predict_quick(self, pil_image: Image.Image) -> dict:
        """Prediction only, without the Grad-CAM heatmap: cheap enough to run for every model
        when the frontend compares models on the same image."""
        img = pil_image.convert("RGB")
        x = eval_transform(img).unsqueeze(0).to(self.device)

        with self._lock, torch.no_grad():
            probs = torch.softmax(self.model(x), dim=1)[0].cpu().numpy()

        idx = int(probs.argmax())
        confidence = float(probs[idx])
        return {
            "label": CLASS_NAMES[idx],
            "confidence": confidence,
            "probabilities": {CLASS_NAMES[i]: float(p) for i, p in enumerate(probs)},
            "low_confidence": confidence < LOW_CONFIDENCE_THRESHOLD,
            "model_name": self.checkpoint_name,
        }
