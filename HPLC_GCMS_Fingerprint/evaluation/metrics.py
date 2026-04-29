"""
Evaluation metrics and recommendation logic for the multi-task pipeline.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    classification_report,
)

import torch


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    target_names: list[str] | None = None,
) -> dict[str, float]:
    """Return accuracy and macro-F1 for a classification head."""
    acc = accuracy_score(y_true, y_pred)
    f1  = f1_score(y_true, y_pred, average="macro", zero_division=0)
    report = classification_report(
        y_true, y_pred,
        target_names=target_names,
        zero_division=0,
    )
    return {"accuracy": acc, "f1_macro": f1, "report": report}


def regression_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_names: list[str] | None = None,
) -> dict:
    """
    Return MAE and RMSE (overall and per-output).

    Parameters
    ----------
    y_true, y_pred : (n_samples, n_outputs) arrays.
    output_names   : names for the outputs (optional).
    """
    mae_overall  = float(mean_absolute_error(y_true, y_pred))
    rmse_overall = float(np.sqrt(mean_squared_error(y_true, y_pred)))

    per_output: list[dict] = []
    for j in range(y_true.shape[1]):
        name = output_names[j] if output_names else str(j)
        mae_j  = float(mean_absolute_error(y_true[:, j], y_pred[:, j]))
        rmse_j = float(np.sqrt(mean_squared_error(y_true[:, j], y_pred[:, j])))
        per_output.append({"name": name, "MAE": mae_j, "RMSE": rmse_j})

    return {
        "MAE_overall":  mae_overall,
        "RMSE_overall": rmse_overall,
        "per_output":   pd.DataFrame(per_output),
    }


# ---------------------------------------------------------------------------
# Full evaluation routines
# ---------------------------------------------------------------------------

def evaluate_ml(
    model,
    test_ds,
) -> dict:
    """
    Evaluate the ML baseline on a test MultiTaskDataset.

    Returns a dict of results for all heads.
    """
    preds = model.predict(test_ds.X)

    results = {}

    # Head 1 – species
    results["species"] = classification_metrics(
        test_ds.species,
        preds["pred_species"],
        target_names=test_ds.species_names,
    )

    # Head 2 – phylum
    results["phylum"] = classification_metrics(
        test_ds.phylum,
        preds["pred_phylum"],
        target_names=test_ds.phylum_names,
    )

    # Head 3 – solvent activity
    results["solvents"] = regression_metrics(
        test_ds.y_solvents,
        preds["pred_solvents"],
        output_names=test_ds.solvent_names,
    )

    # Head 4 – assay performance
    results["assays"] = regression_metrics(
        test_ds.y_assays,
        preds["pred_assays"],
        output_names=test_ds.assay_names,
    )

    # Best-solvent accuracy
    true_best_sol_idx = test_ds.y_solvents.argmax(axis=1)
    results["best_solvent_accuracy"] = float(
        accuracy_score(true_best_sol_idx, preds["best_solvent_idx"])
    )

    # Best-assay accuracy
    true_best_ass_idx = test_ds.y_assays.argmax(axis=1)
    results["best_assay_accuracy"] = float(
        accuracy_score(true_best_ass_idx, preds["best_assay_idx"])
    )

    return results


def evaluate_dl(
    model: "MultiTaskDLModel",
    test_ds,
    device: str | None = None,
) -> dict:
    """
    Evaluate the DL model on a test MultiTaskDataset.
    """
    if device is None:
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        dev = torch.device(device)

    model.eval()
    X_t = torch.tensor(test_ds.X, dtype=torch.float32).to(dev)

    with torch.no_grad():
        out = model.predict(X_t)

    pred_species  = out["pred_species"].cpu().numpy()
    pred_phylum   = out["pred_phylum"].cpu().numpy()
    pred_solvents = out["pred_solvents"].cpu().numpy()
    pred_assays   = out["pred_assays"].cpu().numpy()

    results = {}

    results["species"] = classification_metrics(
        test_ds.species, pred_species, target_names=test_ds.species_names
    )
    results["phylum"] = classification_metrics(
        test_ds.phylum, pred_phylum, target_names=test_ds.phylum_names
    )
    results["solvents"] = regression_metrics(
        test_ds.y_solvents, pred_solvents, output_names=test_ds.solvent_names
    )
    results["assays"] = regression_metrics(
        test_ds.y_assays, pred_assays, output_names=test_ds.assay_names
    )

    true_best_sol_idx = test_ds.y_solvents.argmax(axis=1)
    results["best_solvent_accuracy"] = float(
        accuracy_score(true_best_sol_idx, out["best_solvent_idx"].cpu().numpy())
    )
    true_best_ass_idx = test_ds.y_assays.argmax(axis=1)
    results["best_assay_accuracy"] = float(
        accuracy_score(true_best_ass_idx, out["best_assay_idx"].cpu().numpy())
    )

    return results


# ---------------------------------------------------------------------------
# Pretty-printing
# ---------------------------------------------------------------------------

def print_results(results: dict, model_name: str = "Model") -> None:
    """Print evaluation results in a human-readable format."""
    print(f"\n{'='*60}")
    print(f"  {model_name} – Evaluation Results")
    print(f"{'='*60}")

    sp = results["species"]
    ph = results["phylum"]
    print(f"\n[Classification]")
    print(f"  Species  – Accuracy: {sp['accuracy']:.3f}  F1-macro: {sp['f1_macro']:.3f}")
    print(f"  Phylum   – Accuracy: {ph['accuracy']:.3f}  F1-macro: {ph['f1_macro']:.3f}")

    sol = results["solvents"]
    ass = results["assays"]
    print(f"\n[Regression]")
    print(f"  Solvents – MAE: {sol['MAE_overall']:.4f}  RMSE: {sol['RMSE_overall']:.4f}")
    print(f"  Assays   – MAE: {ass['MAE_overall']:.4f}  RMSE: {ass['RMSE_overall']:.4f}")

    print(f"\n[Recommendation Accuracy]")
    print(f"  Best Solvent: {results['best_solvent_accuracy']:.3f}")
    print(f"  Best Assay:   {results['best_assay_accuracy']:.3f}")
    print()


# ---------------------------------------------------------------------------
# Inference / recommendation for a single new sample
# ---------------------------------------------------------------------------

def recommend(
    model,
    x_new: np.ndarray,
    solvent_names: list[str],
    assay_names: list[str],
    species_names: list[str],
    phylum_names: list[str] | None = None,
    is_dl: bool = False,
    device: str | None = None,
) -> dict:
    """
    Run inference on a single new sample and return recommendations.

    Parameters
    ----------
    model       : fitted MLMultiTaskBaseline or MultiTaskDLModel.
    x_new       : feature vector, shape (n_features,) or (1, n_features).
    is_dl       : True if model is PyTorch.

    Returns
    -------
    dict with:
      'predicted_species', 'predicted_phylum',
      'solvent_activities', 'best_solvent',
      'assay_performances', 'best_assay'
    """
    x = np.atleast_2d(x_new)

    if is_dl:
        dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        xt = torch.tensor(x, dtype=torch.float32).to(dev)
        out = model.predict(xt)
        pred_sp  = int(out["pred_species"].cpu().numpy()[0])
        pred_ph  = int(out["pred_phylum"].cpu().numpy()[0])
        pred_sol = out["pred_solvents"].cpu().numpy()[0]
        pred_ass = out["pred_assays"].cpu().numpy()[0]
        best_sol_idx = int(out["best_solvent_idx"].cpu().numpy()[0])
        best_ass_idx = int(out["best_assay_idx"].cpu().numpy()[0])
    else:
        preds = model.predict(x)
        pred_sp  = int(preds["pred_species"][0])
        pred_ph  = int(preds["pred_phylum"][0])
        pred_sol = preds["pred_solvents"][0]
        pred_ass = preds["pred_assays"][0]
        best_sol_idx = int(preds["best_solvent_idx"][0])
        best_ass_idx = int(preds["best_assay_idx"][0])

    predicted_phylum = (
        phylum_names[pred_ph]
        if phylum_names and pred_ph < len(phylum_names)
        else f"phylum_{pred_ph}"
    )

    return {
        "predicted_species":   species_names[pred_sp],
        "predicted_phylum":    predicted_phylum,
        "solvent_activities":  dict(zip(solvent_names, pred_sol.tolist())),
        "best_solvent":        solvent_names[best_sol_idx],
        "assay_performances":  dict(zip(assay_names, pred_ass.tolist())),
        "best_assay":          assay_names[best_ass_idx],
    }
