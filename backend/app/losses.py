"""Loss functions for the class-imbalance experiments."""
import torch
import torch.nn as nn
import torch.nn.functional as F

LOSS_NAMES = ["ce", "weighted_ce", "focal", "focal_weighted"]


class FocalLoss(nn.Module):
    """Focal loss: down-weights easy examples so training focuses on hard ones."""

    def __init__(self, gamma: float = 2.0, weight: torch.Tensor | None = None):
        super().__init__()
        self.gamma = gamma
        self.register_buffer("weight", weight)

    def forward(self, logits, targets):
        ce = F.cross_entropy(logits, targets, weight=self.weight, reduction="none")
        pt = torch.exp(-F.cross_entropy(logits, targets, reduction="none"))
        return ((1 - pt) ** self.gamma * ce).mean()


def get_loss(name: str, class_weights: torch.Tensor, device) -> nn.Module:
    w = class_weights.to(device)
    if name == "ce":
        return nn.CrossEntropyLoss()
    if name == "weighted_ce":
        return nn.CrossEntropyLoss(weight=w)
    if name == "focal":
        return FocalLoss(gamma=2.0).to(device)
    if name == "focal_weighted":
        return FocalLoss(gamma=2.0, weight=w).to(device)
    raise ValueError(f"Unknown loss '{name}'. Choose from {LOSS_NAMES}")
