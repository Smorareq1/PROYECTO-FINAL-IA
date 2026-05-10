from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.models.base import BaseModel


class CNN2DCommandClassifier(BaseModel):
    def __init__(self, n_classes: int = 6, n_mfcc: int = 13) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.gap = nn.AdaptiveAvgPool2d(1)

        self.dropout = nn.Dropout(0.4)
        self.fc = nn.Linear(128, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, 1, n_mfcc, time)
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.gap(x).flatten(1)
        x = self.dropout(x)
        return self.fc(x)
