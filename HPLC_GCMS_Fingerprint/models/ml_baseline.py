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
from sklearn.pipeline import Pipeline

from .model_registry import build_clf_pipeline, build_reg_pipeline


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
    ) -> "MLMultiTaskBaseline":
        """Train all four heads."""
        print(f"[ML] Training species classifier ({self.clf_type}) …")
        self.head_species.fit(X, species)

        print(f"[ML] Training phylum classifier ({self.clf_type}) …")
        self.head_phylum.fit(X, phylum)

        print(f"[ML] Training solvent-activity regressor ({self.reg_type}) …")
        self.head_solvents.fit(X, y_solvents)

        print(f"[ML] Training assay-performance regressor ({self.reg_type}) …")
        self.head_assays.fit(X, y_assays)

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
