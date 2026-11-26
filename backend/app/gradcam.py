"""Grad-CAM heatmaps."""
import base64
import io

import cv2
import numpy as np
import torch
from PIL import Image


class GradCAM:
    """Grad-CAM using a forward hook on the target layer.

    The model must be in eval mode and called WITHOUT torch.no_grad().
    Call .remove() when finished to detach the hook.
    """

    def __init__(self, model, target_layer):
        self.model = model
        self.activations = None
        self.gradients = None
        self._handle = target_layer.register_forward_hook(self._forward_hook)

    def _forward_hook(self, module, inputs, output):
        self.activations = output.detach()
        output.register_hook(lambda grad: setattr(self, "gradients", grad.detach()))

    def remove(self):
        self._handle.remove()

    def __call__(self, x, class_idx=None):
        self.model.zero_grad(set_to_none=True)
        logits = self.model(x)
        probs = torch.softmax(logits, dim=1)[0].detach().cpu().numpy()
        if class_idx is None:
            class_idx = int(logits.argmax(dim=1).item())
        logits[0, class_idx].backward()

        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = torch.relu((weights * self.activations).sum(dim=1)).squeeze(0)
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        return cam.cpu().numpy(), class_idx, probs


def overlay_heatmap(pil_img: Image.Image, cam: np.ndarray, alpha: float = 0.45,
                    max_side: int = 512) -> Image.Image:
    """Blend a JET-colored heatmap over the (downscaled) original image."""
    img = pil_img.convert("RGB")
    img.thumbnail((max_side, max_side))
    w, h = img.size
    cam_resized = np.clip(cv2.resize(cam, (w, h), interpolation=cv2.INTER_CUBIC), 0, 1)
    heat = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
    heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    blend = (1 - alpha) * np.array(img, dtype=np.float32) + alpha * heat.astype(np.float32)
    return Image.fromarray(np.uint8(np.clip(blend, 0, 255)))


def pil_to_base64(img: Image.Image, fmt: str = "PNG") -> str:
    """Raw base64 string (no data-URI prefix)."""
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
