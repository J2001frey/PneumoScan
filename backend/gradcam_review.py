import argparse
import numpy as np
import torch
import torch.nn.functional as F
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

from app.config import CLASS_NAMES, GRADCAM_DIR, IMG_SIZE, MODEL_DIR, MODEL_FILE
from app.dataset import _collect, eval_transform, get_test_loader
from app.models import build_model


def target_layer(model, name):
    if name == "mobilenetv2":
        return model.features[-1]
    if name.startswith("resnet"):
        return model.layer4[-1]
    raise ValueError(f"Set the last conv layer for '{name}' in target_layer()")


class GradCAM:
    def __init__(self, model, layer):
        self.model, self.act, self.grad = model, None, None
        layer.register_forward_hook(self._fwd)

    def _fwd(self, module, inp, out):
        self.act = out
        if out.requires_grad:          # skipped during the no_grad prediction pass
            out.register_hook(lambda g: setattr(self, "grad", g))

    def __call__(self, x, cls):
        self.model.zero_grad()
        out = self.model(x)
        out[0, cls].backward()
        w = self.grad.mean(dim=(2, 3), keepdim=True)
        cam = F.relu((w * self.act).sum(1, keepdim=True))
        cam = F.interpolate(cam, size=(IMG_SIZE, IMG_SIZE), mode="bilinear", align_corners=False)[0, 0]
        cam = cam - cam.min()
        return (cam / (cam.max() + 1e-8)).detach().cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-file", default=MODEL_FILE)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--max", type=int, default=24, help="images per contact sheet")
    args = ap.parse_args()

    ckpt = torch.load(MODEL_DIR / args.model_file, map_location="cpu")
    model = build_model(ckpt["model_name"], pretrained=False)
    model.load_state_dict(ckpt["state"])
    model.eval()
    cam_fn = GradCAM(model, target_layer(model, ckpt["model_name"]))

    # 1) probabilities for the whole test set (same order as _collect)
    samples = _collect("test")
    probs = []
    with torch.no_grad():
        for x, _ in get_test_loader():
            probs.append(torch.softmax(model(x), 1)[:, 1].numpy())
    probs = np.concatenate(probs)
    labels = np.array([y for _, y in samples])
    preds = (probs >= args.threshold).astype(int)

    # 2) groups: all errors (most confident first) + a few correct ones for reference
    rng = np.random.default_rng(0)
    groups = {
        "FP_false_alarms": np.where((labels == 0) & (preds == 1))[0],
        "FN_missed_pneumonia": np.where((labels == 1) & (preds == 0))[0],
        "TP_correct_pneumonia": rng.permutation(np.where((labels == 1) & (preds == 1))[0]),
        "TN_correct_normal": rng.permutation(np.where((labels == 0) & (preds == 0))[0]),
    }
    for key in ("FP_false_alarms", "FN_missed_pneumonia"):
        idx = groups[key]
        groups[key] = idx[np.argsort(-np.abs(probs[idx] - 0.5))]   # most confident first

    # 3) contact sheets (explains the PREDICTED class)
    for gname, idx in groups.items():
        idx = idx[: args.max]
        if len(idx) == 0:
            continue
        cols = 4
        rows = int(np.ceil(len(idx) / cols))
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.2, rows * 3.4))
        axes = np.atleast_1d(axes).ravel()
        for ax in axes:
            ax.axis("off")
        for ax, i in zip(axes, idx):
            path, y = samples[i]
            pil = Image.open(path).convert("RGB")
            x = eval_transform(pil).unsqueeze(0)
            cam = cam_fn(x, int(preds[i]))
            ax.imshow(pil.resize((IMG_SIZE, IMG_SIZE)))
            ax.imshow(cam, cmap="jet", alpha=0.4)
            ax.set_title(f"true={CLASS_NAMES[y][:4]} pred={CLASS_NAMES[preds[i]][:4]} "
                         f"p={probs[i]:.2f}\n{path.split('/')[-1][:28]}", fontsize=7)
        fig.suptitle(f"{gname} (n={len(groups[gname])}, showing {len(idx)})")
        fig.tight_layout()
        out = GRADCAM_DIR / f"{gname}.png"
        fig.savefig(out, dpi=140)
        plt.close(fig)
        print("saved", out)


if __name__ == "__main__":
    main()