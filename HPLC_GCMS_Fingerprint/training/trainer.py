"""
Training loops for both ML baseline and DL multi-task model.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, TensorDataset

from ..ingestion.dataset import MultiTaskDataset
from ..models.dl_multitask import MultiTaskDLModel
from ..models.ml_baseline import MLMultiTaskBaseline


# ---------------------------------------------------------------------------
# ML trainer
# ---------------------------------------------------------------------------

def train_ml(
    train_ds: MultiTaskDataset,
    n_estimators_clf: int = 300,
    n_estimators_reg: int = 200,
    random_state: int = 42,
) -> MLMultiTaskBaseline:
    """
    Fit the ML multi-task baseline on training data.

    Returns the fitted model.
    """
    model = MLMultiTaskBaseline(
        n_estimators_clf=n_estimators_clf,
        n_estimators_reg=n_estimators_reg,
        random_state=random_state,
    )
    model.fit(
        X          = train_ds.X,
        species    = train_ds.species,
        phylum     = train_ds.phylum,
        y_solvents = train_ds.y_solvents,
        y_assays   = train_ds.y_assays,
    )
    return model


# ---------------------------------------------------------------------------
# DL trainer
# ---------------------------------------------------------------------------

def _to_tensors(ds: MultiTaskDataset, device: torch.device) -> dict[str, torch.Tensor]:
    """Convert dataset arrays to device tensors."""
    return {
        "X":          torch.tensor(ds.X,          dtype=torch.float32).to(device),
        "species":    torch.tensor(ds.species,    dtype=torch.long).to(device),
        "phylum":     torch.tensor(ds.phylum,     dtype=torch.long).to(device),
        "y_solvents": torch.tensor(ds.y_solvents, dtype=torch.float32).to(device),
        "y_assays":   torch.tensor(ds.y_assays,   dtype=torch.float32).to(device),
    }


def train_dl(
    train_ds: MultiTaskDataset,
    val_ds: MultiTaskDataset,
    epochs: int = 200,
    batch_size: int = 32,
    lr: float = 1e-3,
    dropout: float = 0.3,
    patience: int = 30,
    random_state: int = 42,
    device: Optional[str] = None,
) -> tuple[MultiTaskDLModel, list[dict]]:
    """
    Train the PyTorch multi-task model.

    Parameters
    ----------
    train_ds, val_ds : MultiTaskDataset
        Training and validation splits.
    epochs : int
    batch_size : int
    lr : float
        Initial learning rate.
    dropout : float
    patience : int
        Early-stopping patience (epochs without val-loss improvement).
    random_state : int
    device : str, optional
        'cuda', 'mps', or 'cpu'. Auto-detected if None.

    Returns
    -------
    model : trained MultiTaskDLModel
    history : list of per-epoch dicts with loss components.
    """
    torch.manual_seed(random_state)
    np.random.seed(random_state)

    if device is None:
        device_obj = torch.device(
            "cuda" if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available()
            else "cpu"
        )
    else:
        device_obj = torch.device(device)

    print(f"[DL] Training on device: {device_obj}")

    # Build model
    model = MultiTaskDLModel(
        in_dim     = train_ds.X.shape[1],
        n_species  = len(train_ds.species_names),
        n_phyla    = len(train_ds.phylum_names),
        n_solvents = len(train_ds.solvent_names),
        n_assays   = len(train_ds.assay_names),
        dropout    = dropout,
    ).to(device_obj)

    optimizer = Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=10)

    # Prepare DataLoaders
    train_t = _to_tensors(train_ds, device_obj)
    val_t   = _to_tensors(val_ds,   device_obj)

    torch_train_ds = TensorDataset(
        train_t["X"],
        train_t["species"],
        train_t["phylum"],
        train_t["y_solvents"],
        train_t["y_assays"],
    )
    loader = DataLoader(torch_train_ds, batch_size=batch_size, shuffle=True)

    history: list[dict] = []
    best_val_loss = float("inf")
    epochs_no_improve = 0
    best_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_losses: dict[str, float] = {
            k: 0.0 for k in ("species", "phylum", "solvents", "assays", "total")
        }

        for Xb, sp, ph, ys, ya in loader:
            optimizer.zero_grad()
            preds = model(Xb)
            loss, comps = model.compute_loss(
                preds,
                {"species": sp, "phylum": ph, "y_solvents": ys, "y_assays": ya},
            )
            loss.backward()
            optimizer.step()
            for k, v in comps.items():
                epoch_losses[k] += v.item()

        n_batches = len(loader)
        for k in epoch_losses:
            epoch_losses[k] /= n_batches

        # Validation loss
        model.eval()
        with torch.no_grad():
            val_preds = model(val_t["X"])
            val_loss, val_comps = model.compute_loss(
                val_preds,
                {
                    "species":    val_t["species"],
                    "phylum":     val_t["phylum"],
                    "y_solvents": val_t["y_solvents"],
                    "y_assays":   val_t["y_assays"],
                },
            )

        scheduler.step(val_loss.item())

        log = {
            "epoch":    epoch,
            "train":    epoch_losses,
            "val_loss": val_loss.item(),
            **{f"val_{k}": v.item() for k, v in val_comps.items()},
        }
        history.append(log)

        if val_loss.item() < best_val_loss:
            best_val_loss = val_loss.item()
            epochs_no_improve = 0
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            epochs_no_improve += 1

        if epoch % 20 == 0 or epoch == 1:
            print(
                f"  Epoch {epoch:3d}/{epochs}  "
                f"train_total={epoch_losses['total']:.4f}  "
                f"val_total={val_loss.item():.4f}"
            )

        if epochs_no_improve >= patience:
            print(f"  Early stopping at epoch {epoch} (patience={patience}).")
            break

    # Restore best weights
    if best_state is not None:
        model.load_state_dict({k: v.to(device_obj) for k, v in best_state.items()})

    print(f"[DL] Training complete. Best val loss: {best_val_loss:.4f}")
    return model, history
