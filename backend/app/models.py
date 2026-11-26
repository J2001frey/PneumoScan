"""Model zoo: a custom CNN baseline, ResNet50, and MobileNetV2."""
import torch.nn as nn
from torchvision import models

MODEL_NAMES = ["custom_cnn", "resnet50", "mobilenetv2"]


class CustomCNN(nn.Module):
    """Small baseline CNN trained from scratch."""

    def __init__(self, num_classes: int = 2):
        super().__init__()

        def block(cin, cout, pool=True):
            layers = [
                nn.Conv2d(cin, cout, 3, padding=1, bias=False),
                nn.BatchNorm2d(cout),
                nn.ReLU(inplace=False),
            ]
            if pool:
                layers.append(nn.MaxPool2d(2))
            return layers

        self.features = nn.Sequential(
            *block(3, 32), *block(32, 64), *block(64, 128), *block(128, 256, pool=False)
        )  # last module is a ReLU -> used as the Grad-CAM target
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(0.4), nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.classifier(self.pool(self.features(x)))


def build_model(name: str, num_classes: int = 2, pretrained: bool = True) -> nn.Module:
    if name == "custom_cnn":
        return CustomCNN(num_classes)

    if name == "resnet50":
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        m = models.resnet50(weights=weights)
        m.fc = nn.Sequential(nn.Dropout(0.3), nn.Linear(m.fc.in_features, num_classes))
        return m

    if name == "mobilenetv2":
        weights = models.MobileNet_V2_Weights.DEFAULT if pretrained else None
        m = models.mobilenet_v2(weights=weights)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, num_classes)
        return m

    raise ValueError(f"Unknown model '{name}'. Choose from {MODEL_NAMES}")


def get_target_layer(model: nn.Module, name: str) -> nn.Module:
    """Last convolutional stage, used by Grad-CAM."""
    if name == "resnet50":
        return model.layer4[-1]
    if name in ("mobilenetv2", "custom_cnn"):
        return model.features[-1]
    raise ValueError(f"Unknown model '{name}'")
