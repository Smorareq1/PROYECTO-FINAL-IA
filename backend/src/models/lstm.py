from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.models.base import BaseModel


class BiLSTMSequentialClassifier(BaseModel):
    def __init__(self, n_classes: int = 4, n_mfcc: int = 13) -> None:
        super().__init__()
        self.lstm1 = nn.LSTM(
            input_size=n_mfcc,
            hidden_size=64,
            num_layers=1,
            bidirectional=True,
            batch_first=True,
            dropout=0.0,
        )
        self.lstm2 = nn.LSTM(
            input_size=128,
            hidden_size=32,
            num_layers=1,
            bidirectional=True,
            batch_first=True,
        )
        self.dropout = nn.Dropout(0.4)
        self.fc1 = nn.Linear(64, 32)
        self.fc2 = nn.Linear(32, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, time, n_mfcc)
        x, _ = self.lstm1(x)
        x = F.dropout(x, 0.3, self.training)
        x, (h_n, _) = self.lstm2(x)
        forward_h = h_n[-2, :, :]
        backward_h = h_n[-1, :, :]
        h = torch.cat([forward_h, backward_h], dim=1)
        h = self.dropout(h)
        h = F.relu(self.fc1(h))
        return self.fc2(h)
