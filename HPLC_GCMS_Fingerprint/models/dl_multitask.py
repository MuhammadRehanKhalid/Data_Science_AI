"""
PyTorch multi-task deep-learning model.

Architecture
------------
  SharedEncoder
    Input  → BatchNorm → Linear(in, 256) → ReLU → Dropout
           → Linear(256, 128)            → ReLU → Dropout
           → Linear(128, 64)             → ReLU
           → latent Z (64-dim)

  Head 1 – Species classifier
    Z → Linear(64, 32) → ReLU → Linear(32, n_species) [logits for CrossEntropy]

  Head 2 – Phylum classifier
    Z → Linear(64, 32) → ReLU → Linear(32, n_phyla)   [logits for CrossEntropy]

  Head 3 – Solvent-activity regressor
    Z → Linear(64, 32) → ReLU → Linear(32, n_solvents) [sigmoid → [0,1]]

  Head 4 – Assay-performance regressor
    Z → Linear(64, 32) → ReLU → Linear(32, n_assays)   [sigmoid → [0,1]]

Joint loss
----------
  total = α * CE_species + β * CE_phylum + γ * MSE_solvents + δ * MSE_assays
"""

from __future__ import annotations

import torch
import torch.nn as nn


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

class SharedEncoder(nn.Module):
    """Shared feature encoder: raw features → latent Z."""

    def __init__(self, in_dim: int, dropout: float = 0.3) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.BatchNorm1d(in_dim),
            nn.Linear(in_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ClassificationHead(nn.Module):
    """Dense head for multi-class classification."""

    def __init__(self, in_dim: int, n_classes: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 32),
            nn.ReLU(),
            nn.Linear(32, n_classes),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z)   # logits (no softmax; use CrossEntropyLoss)


class RegressionHead(nn.Module):
    """Dense head for bounded multi-output regression [0, 1]."""

    def __init__(self, in_dim: int, n_outputs: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 32),
            nn.ReLU(),
            nn.Linear(32, n_outputs),
            nn.Sigmoid(),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        return self.net(z)


# ---------------------------------------------------------------------------
# Multi-task model
# ---------------------------------------------------------------------------

class MultiTaskDLModel(nn.Module):
    """
    Multi-task neural network with shared encoder and four task heads.

    Parameters
    ----------
    in_dim : int
        Number of input features.
    n_species : int
        Number of species classes (Head 1).
    n_phyla : int
        Number of phylum classes (Head 2).
    n_solvents : int
        Number of solvents (Head 3 regression outputs).
    n_assays : int
        Number of assays (Head 4 regression outputs).
    dropout : float
        Dropout rate in the encoder.
    loss_weights : dict, optional
        Weights for each loss term.  Keys: 'species', 'phylum', 'solvents', 'assays'.
    """

    DEFAULT_LOSS_WEIGHTS = {
        "species":  1.0,
        "phylum":   0.5,
        "solvents": 1.0,
        "assays":   0.8,
    }

    def __init__(
        self,
        in_dim: int,
        n_species: int,
        n_phyla: int,
        n_solvents: int,
        n_assays: int,
        dropout: float = 0.3,
        loss_weights: dict[str, float] | None = None,
    ) -> None:
        super().__init__()

        self.encoder = SharedEncoder(in_dim, dropout=dropout)

        latent_dim = 64
        self.head_species  = ClassificationHead(latent_dim, n_species)
        self.head_phylum   = ClassificationHead(latent_dim, n_phyla)
        self.head_solvents = RegressionHead(latent_dim, n_solvents)
        self.head_assays   = RegressionHead(latent_dim, n_assays)

        # Loss functions
        self.ce_loss  = nn.CrossEntropyLoss()
        self.mse_loss = nn.MSELoss()

        self.loss_weights = loss_weights or self.DEFAULT_LOSS_WEIGHTS

        # Store metadata
        self.n_species  = n_species
        self.n_phyla    = n_phyla
        self.n_solvents = n_solvents
        self.n_assays   = n_assays

    # ------------------------------------------------------------------

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        z = self.encoder(x)
        return {
            "species":  self.head_species(z),
            "phylum":   self.head_phylum(z),
            "solvents": self.head_solvents(z),
            "assays":   self.head_assays(z),
        }

    def compute_loss(
        self,
        preds: dict[str, torch.Tensor],
        targets: dict[str, torch.Tensor],
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        """
        Compute weighted multi-task loss.

        Parameters
        ----------
        preds   : dict from ``forward()``.
        targets : dict with keys 'species', 'phylum', 'y_solvents', 'y_assays'.

        Returns
        -------
        total_loss : scalar tensor
        loss_components : dict of individual loss tensors (for logging).
        """
        l_species  = self.ce_loss(preds["species"],  targets["species"])
        l_phylum   = self.ce_loss(preds["phylum"],   targets["phylum"])
        l_solvents = self.mse_loss(preds["solvents"], targets["y_solvents"])
        l_assays   = self.mse_loss(preds["assays"],   targets["y_assays"])

        w = self.loss_weights
        total = (
            w["species"]  * l_species
            + w["phylum"] * l_phylum
            + w["solvents"] * l_solvents
            + w["assays"]   * l_assays
        )

        components = {
            "species":  l_species,
            "phylum":   l_phylum,
            "solvents": l_solvents,
            "assays":   l_assays,
            "total":    total,
        }
        return total, components

    # ------------------------------------------------------------------
    # Convenience prediction (no grad)

    @torch.no_grad()
    def predict(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        self.eval()
        preds = self.forward(x)
        return {
            "pred_species":     preds["species"].argmax(dim=1),
            "pred_phylum":      preds["phylum"].argmax(dim=1),
            "pred_solvents":    preds["solvents"],
            "pred_assays":      preds["assays"],
            "best_solvent_idx": preds["solvents"].argmax(dim=1),
            "best_assay_idx":   preds["assays"].argmax(dim=1),
        }
