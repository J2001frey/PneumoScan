"""Train a model on the local dataset.

Examples (run from backend/):
    python train.py --model custom_cnn --loss weighted_ce
    python train.py --model resnet50 --loss weighted_ce
    python train.py --model mobilenetv2 --loss focal
"""
import argparse
import json
import random
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import f1_score, recall_score

from app.config import CLASS_NAMES, IMG_SIZE, MODEL_DIR, OUTPUT_DIR, PLOTS_DIR, SEED, get_device
from app.dataset import get_loaders
from app.losses import LOSS_NAMES, get_loss
from app.models import MODEL_NAMES, build_model


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def run_epoch(model, loader, criterion, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    total_loss, preds, labels = 0.0, [], []
    with torch.set_grad_enabled(training):
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            loss = criterion(out, y)
            if training:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * x.size(0)
            preds.extend(out.argmax(1).cpu().tolist())
            labels.extend(y.cpu().tolist())
    n = len(labels)
    acc = float(np.mean(np.array(preds) == np.array(labels)))
    f1 = f1_score(labels, preds, average="macro", zero_division=0)
    recall = recall_score(labels, preds, pos_label=1, zero_division=0)
    return total_loss / n, acc, f1, recall


def save_curves(history, name):
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(history["train_loss"], label="train")
    ax[0].plot(history["val_loss"], label="val")
    ax[0].set_title("Loss"); ax[0].set_xlabel("epoch"); ax[0].legend()
    ax[1].plot(history["val_f1"], label="val macro-F1")
    ax[1].plot(history["val_recall"], label="val pneumonia recall")
    ax[1].set_title("Validation metrics"); ax[1].set_xlabel("epoch"); ax[1].legend()
    fig.suptitle(name)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / f"curves_{name}.png", dpi=150)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=MODEL_NAMES, default="resnet50")
    p.add_argument("--loss", choices=LOSS_NAMES, default="weighted_ce")
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--lr", type=float, default=None)
    p.add_argument("--patience", type=int, default=4, help="early-stopping patience")
    args = p.parse_args()

    lr = args.lr or (1e-3 if args.model == "custom_cnn" else 1e-4)
    name = f"{args.model}_{args.loss}"
    set_seed(SEED)
    device = get_device()
    print(f"Device: {device} | Run: {name} | lr={lr}")

    data = get_loaders()
    print(f"Samples per class (NORMAL, PNEUMONIA) -> {data['counts']}")
    print(f"Class weights: {data['class_weights'].tolist()}")

    model = build_model(args.model, pretrained=True).to(device)
    criterion = get_loss(args.loss, data["class_weights"], device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    history = {k: [] for k in ["train_loss", "val_loss", "val_acc", "val_f1", "val_recall"]}
    best_f1, best_epoch, bad_epochs = -1.0, 0, 0
    ckpt_path = MODEL_DIR / f"{name}.pt"

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        tr_loss, _, _, _ = run_epoch(model, data["train"], criterion, device, optimizer)
        va_loss, va_acc, va_f1, va_rec = run_epoch(model, data["val"], criterion, device)
        scheduler.step()

        for k, v in zip(history, [tr_loss, va_loss, va_acc, va_f1, va_rec]):
            history[k].append(float(v))
        print(f"Epoch {epoch:02d}/{args.epochs} | train_loss {tr_loss:.4f} | val_loss {va_loss:.4f} "
              f"| val_acc {va_acc:.3f} | val_f1 {va_f1:.3f} | val_recall {va_rec:.3f} "
              f"| {time.time() - t0:.0f}s")

        if va_f1 > best_f1:
            best_f1, best_epoch, bad_epochs = va_f1, epoch, 0
            torch.save({
                "state": model.state_dict(),
                "classes": CLASS_NAMES,
                "model_name": args.model,
                "loss_name": args.loss,
                "img_size": IMG_SIZE,
                "best_val_f1": best_f1,
                "epoch": epoch,
            }, ckpt_path)
        else:
            bad_epochs += 1
            if bad_epochs >= args.patience:
                print(f"Early stopping (no improvement for {args.patience} epochs).")
                break

    with open(OUTPUT_DIR / f"history_{name}.json", "w") as f:
        json.dump(history, f, indent=2)
    save_curves(history, name)
    print(f"Best val macro-F1 {best_f1:.3f} at epoch {best_epoch}. Saved -> {ckpt_path}")


if __name__ == "__main__":  # guard needed for DataLoader workers on macOS/Windows
    main()
