"""Local dataset loading.

Reads images straight from backend/data/chest_xray.

Expected layout (the 'val' folder is OPTIONAL):
    chest_xray/
        train/{NORMAL,PNEUMONIA}
        test/{NORMAL,PNEUMONIA}
        val/{NORMAL,PNEUMONIA}      <- optional, merged into train if present

A fresh stratified validation split is carved out of the training images, so the
tiny original val folder is never needed. The test folder is left untouched.
"""
from pathlib import Path

import torch
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, transforms

from app.config import (
    BATCH_SIZE, CLASS_NAMES, DATA_DIR, IMG_SIZE, NUM_WORKERS, SEED, VAL_FRACTION,
)

MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]

train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomRotation(10),
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.85, 1.0)),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(MEAN, STD),
])


class XRayDataset(Dataset):
    """Dataset over a list of (image_path, label) pairs."""

    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")  # X-rays are grayscale -> 3 channels
        if self.transform:
            img = self.transform(img)
        return img, label


def _collect(split: str, required: bool = True):
    """Return [(path, label), ...] for DATA_DIR/split, or [] if optional and absent."""
    folder = Path(DATA_DIR) / split
    if not folder.exists():
        if not required:
            return []
        found = sorted(p.name for p in Path(DATA_DIR).glob("*")) if Path(DATA_DIR).exists() else []
        raise FileNotFoundError(
            f"Dataset folder not found: {folder}\n"
            f"Folders found in {DATA_DIR}: {found}\n"
            "Expected backend/data/chest_xray/{train,test}/{NORMAL,PNEUMONIA} (val is optional)."
        )
    ds = datasets.ImageFolder(folder)
    if ds.classes != CLASS_NAMES:
        raise ValueError(f"Expected classes {CLASS_NAMES} in {folder}, found {ds.classes}")
    return ds.samples


def compute_class_weights(labels, num_classes: int = 2) -> torch.Tensor:
    """Inverse-frequency weights: rarer class gets a larger weight."""
    counts = torch.bincount(torch.tensor(labels), minlength=num_classes).float()
    return counts.sum() / (num_classes * counts)


def get_loaders(batch_size: int = BATCH_SIZE) -> dict:
    all_train = _collect("train")
    for extra in ("val", "valid", "validation"):  # optional original validation folder
        all_train += _collect(extra, required=False)

    labels = [y for _, y in all_train]
    train_s, val_s = train_test_split(
        all_train, test_size=VAL_FRACTION, stratify=labels, random_state=SEED
    )
    test_s = _collect("test")

    train_labels = [y for _, y in train_s]
    kw = dict(batch_size=batch_size, num_workers=NUM_WORKERS)
    return {
        "train": DataLoader(XRayDataset(train_s, train_transform), shuffle=True, **kw),
        "val": DataLoader(XRayDataset(val_s, eval_transform), shuffle=False, **kw),
        "test": DataLoader(XRayDataset(test_s, eval_transform), shuffle=False, **kw),
        "class_weights": compute_class_weights(train_labels),
        "counts": {
            "train": torch.bincount(torch.tensor(train_labels)).tolist(),
            "val": torch.bincount(torch.tensor([y for _, y in val_s])).tolist(),
            "test": torch.bincount(torch.tensor([y for _, y in test_s])).tolist(),
        },
    }


def get_test_loader(batch_size: int = BATCH_SIZE) -> DataLoader:
    test_s = _collect("test")
    return DataLoader(
        XRayDataset(test_s, eval_transform),
        batch_size=batch_size, shuffle=False, num_workers=NUM_WORKERS,
    )