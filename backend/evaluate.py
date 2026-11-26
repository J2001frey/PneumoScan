"""Evaluate saved models on the held-out test set.

    python evaluate.py                                  # every .pt in saved_models/
    python evaluate.py --model_file resnet50_weighted_ce.pt
Writes outputs/metrics.json plus confusion-matrix and ROC plots.
"""
import argparse
import json
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score, roc_curve,
)

from app.config import CLASS_NAMES, MODEL_DIR, OUTPUT_DIR, PLOTS_DIR, get_device
from app.dataset import get_test_loader
from app.models import build_model


def load_checkpoint(path, device):
    ckpt = torch.load(path, map_location=device)
    model = build_model(ckpt["model_name"], pretrained=False)
    model.load_state_dict(ckpt["state"])
    return model.to(device).eval(), ckpt


@torch.no_grad()
def predict_loader(model, loader, device):
    y_true, y_prob, fwd_time = [], [], 0.0
    for x, y in loader:
        x = x.to(device)
        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        out = model(x)
        if device.type == "cuda":
            torch.cuda.synchronize()
        fwd_time += time.perf_counter() - t0
        y_prob.extend(torch.softmax(out, 1)[:, 1].cpu().tolist())
        y_true.extend(y.tolist())
    return np.array(y_true), np.array(y_prob), fwd_time


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model_file", default=None)
    p.add_argument("--threshold", type=float, default=0.5)
    args = p.parse_args()

    device = get_device()
    files = [MODEL_DIR / args.model_file] if args.model_file else sorted(MODEL_DIR.glob("*.pt"))
    if not files:
        raise SystemExit("No .pt files in saved_models/. Run train.py first.")

    loader = get_test_loader()
    results, rocs = {}, {}

    for path in files:
        name = path.stem
        model, ckpt = load_checkpoint(path, device)
        y_true, y_prob, fwd = predict_loader(model, loader, device)
        y_pred = (y_prob >= args.threshold).astype(int)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

        results[name] = {
            "model": ckpt["model_name"],
            "loss": ckpt["loss_name"],
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall_sensitivity": recall_score(y_true, y_pred, zero_division=0),
            "specificity": cm[0, 0] / max(cm[0].sum(), 1),
            "f1": f1_score(y_true, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_true, y_prob),
            "confusion_matrix": cm.tolist(),
            "ms_per_image": 1000 * fwd / len(y_true),
            "parameters_millions": sum(p_.numel() for p_ in model.parameters()) / 1e6,
            "file_size_mb": path.stat().st_size / 1e6,
        }
        rocs[name] = roc_curve(y_true, y_prob)

        fig, ax = plt.subplots(figsize=(4, 3.5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False,
                    xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, ax=ax)
        ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title(name)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / f"confusion_{name}.png", dpi=150)
        plt.close(fig)

        r = results[name]
        print(f"{name:28s} acc {r['accuracy']:.3f} | recall {r['recall_sensitivity']:.3f} | "
              f"prec {r['precision']:.3f} | F1 {r['f1']:.3f} | AUC {r['roc_auc']:.3f} | "
              f"{r['ms_per_image']:.1f} ms/img")

    fig, ax = plt.subplots(figsize=(5.5, 5))
    for name, (fpr, tpr, _) in rocs.items():
        ax.plot(fpr, tpr, label=f"{name} (AUC {results[name]['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
    ax.set_title("ROC curves (test set)"); ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "roc_comparison.png", dpi=150)
    plt.close(fig)

    with open(OUTPUT_DIR / "metrics.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved metrics -> {OUTPUT_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
