"""
Scikit-learn multi-task baseline.

Three separate sklearn pipelines address the three heads:
  Head 1 – Species/phylum classification  (configurable; default: RandomForestClassifier)
  Head 2 – Solvent activity regression    (configurable; default: MultiOutputRegressor + GBR)
  Head 3 – Assay performance regression   (configurable; default: MultiOutputRegressor + GBR)

Each pipeline wraps a StandardScaler and the chosen estimator.
Available types are defined in models/model_registry.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline

from .model_registry import build_clf_pipeline, build_reg_pipeline


def pack_multitask_targets(
    species: np.ndarray,
    phylum: np.ndarray,
    y_solvents: np.ndarray,
    y_assays: np.ndarray,
) -> np.ndarray:
    """Pack multi-task targets into a 1D object array for sklearn search CV."""
    packed = [
        (
            int(species[i]),
            int(phylum[i]),
            np.asarray(y_solvents[i], dtype=float),
            np.asarray(y_assays[i], dtype=float),
        )
        for i in range(len(species))
    ]
    return np.asarray(packed, dtype=object)


def unpack_multitask_targets(
    y: np.ndarray | list | tuple,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Unpack packed multi-task targets back into their component arrays."""
    if isinstance(y, dict):
        return (
            np.asarray(y["species"]),
            np.asarray(y["phylum"]),
            np.asarray(y["y_solvents"]),
            np.asarray(y["y_assays"]),
        )

    y_arr = np.asarray(y, dtype=object)
    species: list[int] = []
    phylum: list[int] = []
    y_solvents: list[np.ndarray] = []
    y_assays: list[np.ndarray] = []

    for item in y_arr:
        if isinstance(item, dict):
            species.append(int(item["species"]))
            phylum.append(int(item["phylum"]))
            y_solvents.append(np.asarray(item["y_solvents"], dtype=float))
            y_assays.append(np.asarray(item["y_assays"], dtype=float))
            continue

        sp, ph, ys, ya = item
        species.append(int(sp))
        phylum.append(int(ph))
        y_solvents.append(np.asarray(ys, dtype=float))
        y_assays.append(np.asarray(ya, dtype=float))

    return (
        np.asarray(species),
        np.asarray(phylum),
        np.asarray(y_solvents),
        np.asarray(y_assays),
    )


def score_multitask_predictions(
    y_true: np.ndarray | list | tuple,
    y_pred: dict[str, np.ndarray],
) -> float:
    """Score predictions using the same aggregate utility as the pipeline."""
    species, phylum, y_solvents, y_assays = unpack_multitask_targets(y_true)

    species_acc = accuracy_score(species, y_pred["pred_species"])
    species_f1 = f1_score(species, y_pred["pred_species"], average="macro", zero_division=0)
    phylum_acc = accuracy_score(phylum, y_pred["pred_phylum"])
    phylum_f1 = f1_score(phylum, y_pred["pred_phylum"], average="macro", zero_division=0)

    solvent_mae = mean_absolute_error(y_solvents, y_pred["pred_solvents"])
    solvent_rmse = float(np.sqrt(mean_squared_error(y_solvents, y_pred["pred_solvents"])))
    assay_mae = mean_absolute_error(y_assays, y_pred["pred_assays"])
    assay_rmse = float(np.sqrt(mean_squared_error(y_assays, y_pred["pred_assays"])))

    true_best_sol_idx = y_solvents.argmax(axis=1)
    true_best_ass_idx = y_assays.argmax(axis=1)
    best_sol_acc = accuracy_score(true_best_sol_idx, y_pred["best_solvent_idx"])
    best_ass_acc = accuracy_score(true_best_ass_idx, y_pred["best_assay_idx"])

    cls_terms = [
        float(species_acc),
        float(species_f1),
        float(phylum_acc),
        float(phylum_f1),
        float(best_sol_acc),
        float(best_ass_acc),
    ]
    reg_terms = [
        1.0 / (1.0 + float(solvent_mae)),
        1.0 / (1.0 + float(solvent_rmse)),
        1.0 / (1.0 + float(assay_mae)),
        1.0 / (1.0 + float(assay_rmse)),
    ]
    return float(np.mean(cls_terms + reg_terms))


# ---------------------------------------------------------------------------
# Multi-task baseline wrapper
# ---------------------------------------------------------------------------

@dataclass
class MLMultiTaskBaseline:
    """
    Wrapper that trains three independent sklearn pipelines:
      - head_species  : configurable classifier for species
      - head_phylum   : configurable classifier for phylum
      - head_solvents : configurable multi-output regressor for solvent activity
      - head_assays   : configurable multi-output regressor for assay performance

    Parameters
    ----------
    clf_type : str
        Classifier type key (see model_registry._CLF_TYPES).
    reg_type : str
        Regressor type key (see model_registry._REG_TYPES).
    n_estimators_clf : int
    n_estimators_reg : int
    random_state : int
    """

    clf_type:         str = "random_forest"
    reg_type:         str = "gradient_boosting"
    n_estimators_clf: int = 300
    n_estimators_reg: int = 200
    random_state:     int = 42

    head_species:  Pipeline = field(init=False)
    head_phylum:   Pipeline = field(init=False)
    head_solvents: Pipeline = field(init=False)
    head_assays:   Pipeline = field(init=False)

    def __post_init__(self) -> None:
        self.head_species = build_clf_pipeline(
            self.clf_type, self.n_estimators_clf, self.random_state
        )
        self.head_phylum = build_clf_pipeline(
            self.clf_type, self.n_estimators_clf, self.random_state
        )
        self.head_solvents = build_reg_pipeline(
            self.reg_type, self.n_estimators_reg, self.random_state
        )
        self.head_assays = build_reg_pipeline(
            self.reg_type, self.n_estimators_reg, self.random_state
        )

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        X: np.ndarray,
        species: np.ndarray,
        phylum: np.ndarray,
        y_solvents: np.ndarray,
        y_assays: np.ndarray,
        progress_callback: callable | None = None,
        verbose: bool = True,
    ) -> "MLMultiTaskBaseline":
        """Train all four heads."""
        if progress_callback is not None:
            try:
                progress_callback(0.0, {"stage": "ml_start", "message": "Training species classifier"})
            except Exception:
                pass

        if verbose:
            print(f"[ML] Training species classifier ({self.clf_type}) …")
        self.head_species.fit(X, species)
        if progress_callback is not None:
            try:
                progress_callback(25.0, {"stage": "ml_species_complete", "message": "Species classifier complete"})
            except Exception:
                pass

        if verbose:
            print(f"[ML] Training phylum classifier ({self.clf_type}) …")
        self.head_phylum.fit(X, phylum)
        if progress_callback is not None:
            try:
                progress_callback(50.0, {"stage": "ml_phylum_complete", "message": "Phylum classifier complete"})
            except Exception:
                pass

        if verbose:
            print(f"[ML] Training solvent-activity regressor ({self.reg_type}) …")
        self.head_solvents.fit(X, y_solvents)
        if progress_callback is not None:
            try:
                progress_callback(75.0, {"stage": "ml_solvents_complete", "message": "Solvent regressor complete"})
            except Exception:
                pass

        if verbose:
            print(f"[ML] Training assay-performance regressor ({self.reg_type}) …")
        self.head_assays.fit(X, y_assays)
        if progress_callback is not None:
            try:
                progress_callback(100.0, {"stage": "ml_assays_complete", "message": "Assay regressor complete"})
            except Exception:
                pass

        return self

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, X: np.ndarray) -> dict[str, np.ndarray]:
        """
        Run all heads and return a result dict.

        Keys
        ----
        pred_species     : int array (n_samples,)
        pred_phylum      : int array (n_samples,)
        pred_solvents    : float array (n_samples, n_solvents)
        pred_assays      : float array (n_samples, n_assays)
        best_solvent_idx : int array  (n_samples,)
        best_assay_idx   : int array  (n_samples,)
        """
        pred_species  = self.head_species.predict(X)
        pred_phylum   = self.head_phylum.predict(X)
        pred_solvents = np.clip(self.head_solvents.predict(X), 0.0, 1.0)
        pred_assays   = np.clip(self.head_assays.predict(X), 0.0, 1.0)

        return {
            "pred_species":     pred_species,
            "pred_phylum":      pred_phylum,
            "pred_solvents":    pred_solvents,
            "pred_assays":      pred_assays,
            "best_solvent_idx": pred_solvents.argmax(axis=1),
            "best_assay_idx":   pred_assays.argmax(axis=1),
        }

    def predict_proba_species(self, X: np.ndarray) -> np.ndarray:
        """Return species class probabilities (only available for probabilistic classifiers)."""
        estimator = self.head_species.named_steps.get("clf")
        if hasattr(estimator, "predict_proba"):
            return self.head_species.predict_proba(X)
        raise AttributeError(
            f"The '{self.clf_type}' classifier does not support predict_proba."
        )


class MLMultiTaskSearchEstimator(BaseEstimator):
    """Sklearn-compatible wrapper used for GridSearchCV / RandomizedSearchCV."""

    def __init__(
        self,
        clf_type: str = "random_forest",
        reg_type: str = "gradient_boosting",
        n_estimators_clf: int = 300,
        n_estimators_reg: int = 200,
        random_state: int = 42,
    ) -> None:
        self.clf_type = clf_type
        self.reg_type = reg_type
        self.n_estimators_clf = n_estimators_clf
        self.n_estimators_reg = n_estimators_reg
        self.random_state = random_state

    def fit(self, X: np.ndarray, y: np.ndarray | list | tuple) -> "MLMultiTaskSearchEstimator":
        species, phylum, y_solvents, y_assays = unpack_multitask_targets(y)
        self.model_ = MLMultiTaskBaseline(
            clf_type=self.clf_type,
            reg_type=self.reg_type,
            n_estimators_clf=self.n_estimators_clf,
            n_estimators_reg=self.n_estimators_reg,
            random_state=self.random_state,
        )
        self.model_.fit(X, species, phylum, y_solvents, y_assays)
        return self

    def predict(self, X: np.ndarray) -> dict[str, np.ndarray]:
        return self.model_.predict(X)

    def score(self, X: np.ndarray, y: np.ndarray | list | tuple) -> float:
        return score_multitask_predictions(y, self.predict(X))
