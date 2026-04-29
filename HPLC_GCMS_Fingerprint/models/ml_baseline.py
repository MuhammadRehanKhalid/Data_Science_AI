"""
Scikit-learn multi-task baseline.

Three separate sklearn pipelines address the three heads:
  Head 1 – Species/phylum classification  (RandomForestClassifier)
  Head 2 – Solvent activity regression    (MultiOutputRegressor + GBR)
  Head 3 – Assay performance regression   (MultiOutputRegressor + GBR)

Each pipeline wraps a StandardScaler (re-applied inside, so the external
scaler in the dataset is idempotent here) and the estimator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def _make_clf_pipeline(n_estimators: int = 300, random_state: int = 42) -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=None,
            min_samples_leaf=1,
            random_state=random_state,
            n_jobs=-1,
        )),
    ])


def _make_regressor_pipeline(
    n_estimators: int = 200,
    learning_rate: float = 0.05,
    max_depth: int = 4,
    random_state: int = 42,
) -> Pipeline:
    base_gbr = GradientBoostingRegressor(
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        random_state=random_state,
    )
    return Pipeline([
        ("scaler", StandardScaler()),
        ("reg", MultiOutputRegressor(base_gbr, n_jobs=-1)),
    ])


# ---------------------------------------------------------------------------
# Multi-task baseline wrapper
# ---------------------------------------------------------------------------

@dataclass
class MLMultiTaskBaseline:
    """
    Wrapper that trains three independent sklearn pipelines:
      - head_species  : RandomForest species classifier
      - head_phylum   : RandomForest phylum classifier
      - head_solvents : Multi-output GBR solvent-activity regressor
      - head_assays   : Multi-output GBR assay-performance regressor
    """

    n_estimators_clf: int = 300
    n_estimators_reg: int = 200
    random_state: int = 42

    head_species:  Pipeline = field(init=False)
    head_phylum:   Pipeline = field(init=False)
    head_solvents: Pipeline = field(init=False)
    head_assays:   Pipeline = field(init=False)

    def __post_init__(self) -> None:
        self.head_species  = _make_clf_pipeline(self.n_estimators_clf, self.random_state)
        self.head_phylum   = _make_clf_pipeline(self.n_estimators_clf, self.random_state)
        self.head_solvents = _make_regressor_pipeline(self.n_estimators_reg, random_state=self.random_state)
        self.head_assays   = _make_regressor_pipeline(self.n_estimators_reg, random_state=self.random_state)

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
        print("[ML] Training species classifier …")
        self.head_species.fit(X, species)

        print("[ML] Training phylum classifier …")
        self.head_phylum.fit(X, phylum)

        print("[ML] Training solvent-activity regressor …")
        self.head_solvents.fit(X, y_solvents)

        print("[ML] Training assay-performance regressor …")
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
        """Return species class probabilities."""
        return self.head_species.predict_proba(X)
