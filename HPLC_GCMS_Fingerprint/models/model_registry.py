"""
Model registry for the HPLC / GC-MS multi-task pipeline.

This module provides:
  1. A catalogue of available sklearn estimators for the ML heads.
  2. ``build_clf_pipeline`` / ``build_reg_pipeline`` factories that return
     a ready-to-fit sklearn Pipeline for the requested model type.
  3. ``recommend_model`` – prints data-driven guidance on which model to choose
     and why, based on sample count, feature dimensionality, GPU availability
     and the multi-task nature of the problem.

Available model keys
--------------------
Classifiers (--ml-clf / head_species & head_phylum):
  random_forest       – RandomForestClassifier         (default, robust)
  gradient_boosting   – GradientBoostingClassifier     (high accuracy, slower)
  svm                 – SVC                            (good for small data, high-dim)
  knn                 – KNeighborsClassifier           (simple, interpretable)
  logistic_regression – LogisticRegression (L2 ridge)  (fast baseline)

Regressors (--ml-reg / head_solvents & head_assays):
  gradient_boosting   – GradientBoostingRegressor / MOR  (default, accurate)
  random_forest       – RandomForestRegressor / MOR       (fast, robust)
  ridge               – Ridge                            (linear, fast, high-dim)
  lasso               – Lasso                            (linear + feature selection)
  svm                 – SVR / MOR                        (good for small data)
  knn                 – KNeighborsRegressor / MOR        (simple baseline)

Deep-learning model (--dl-model):
  mlp / ann           – Multi-layer Perceptron (current default shared encoder)
  cnn                 – 1-D Convolutional encoder operating on spectral features
                        (see models/dl_multitask.py, CNNMultiTaskDLModel)
"""

from __future__ import annotations

from typing import Any

from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import Lasso, LogisticRegression, Ridge
from sklearn.multioutput import MultiOutputRegressor
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR


# ---------------------------------------------------------------------------
# Classifier factory
# ---------------------------------------------------------------------------

_CLF_TYPES = {
    "random_forest",
    "gradient_boosting",
    "svm",
    "knn",
    "logistic_regression",
}

_REG_TYPES = {
    "gradient_boosting",
    "random_forest",
    "ridge",
    "lasso",
    "svm",
    "knn",
}


def build_clf_pipeline(
    clf_type: str = "random_forest",
    n_estimators: int = 300,
    random_state: int = 42,
) -> Pipeline:
    """Return a StandardScaler + classifier Pipeline for the requested type."""
    clf_type = clf_type.lower()
    if clf_type not in _CLF_TYPES:
        raise ValueError(
            f"Unknown classifier type '{clf_type}'. "
            f"Choose from: {sorted(_CLF_TYPES)}"
        )

    if clf_type == "random_forest":
        est = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=None,
            min_samples_leaf=1,
            random_state=random_state,
            n_jobs=-1,
        )
    elif clf_type == "gradient_boosting":
        est = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=0.05,
            max_depth=4,
            random_state=random_state,
        )
    elif clf_type == "svm":
        est = SVC(kernel="rbf", C=1.0, gamma="scale", probability=True,
                  random_state=random_state)
    elif clf_type == "knn":
        est = KNeighborsClassifier(n_neighbors=5, n_jobs=-1)
    elif clf_type == "logistic_regression":
        est = LogisticRegression(
            C=1.0, max_iter=1000, random_state=random_state, n_jobs=-1
        )

    return Pipeline([("scaler", StandardScaler()), ("clf", est)])


# ---------------------------------------------------------------------------
# Regressor factory
# ---------------------------------------------------------------------------

def build_reg_pipeline(
    reg_type: str = "gradient_boosting",
    n_estimators: int = 200,
    random_state: int = 42,
) -> Pipeline:
    """Return a StandardScaler + MultiOutputRegressor Pipeline for the requested type."""
    reg_type = reg_type.lower()
    if reg_type not in _REG_TYPES:
        raise ValueError(
            f"Unknown regressor type '{reg_type}'. "
            f"Choose from: {sorted(_REG_TYPES)}"
        )

    if reg_type == "gradient_boosting":
        base = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=0.05,
            max_depth=4,
            random_state=random_state,
        )
        est: Any = MultiOutputRegressor(base, n_jobs=-1)
    elif reg_type == "random_forest":
        base = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=None,
            min_samples_leaf=1,
            random_state=random_state,
            n_jobs=-1,
        )
        est = MultiOutputRegressor(base, n_jobs=-1)
    elif reg_type == "ridge":
        est = Ridge(alpha=1.0)
    elif reg_type == "lasso":
        est = Lasso(alpha=0.01, max_iter=5000)
    elif reg_type == "svm":
        base = SVR(kernel="rbf", C=1.0, gamma="scale")
        est = MultiOutputRegressor(base, n_jobs=-1)
    elif reg_type == "knn":
        base = KNeighborsRegressor(n_neighbors=5, n_jobs=-1)
        est = MultiOutputRegressor(base, n_jobs=-1)

    return Pipeline([("scaler", StandardScaler()), ("reg", est)])


# ---------------------------------------------------------------------------
# Model recommendation engine
# ---------------------------------------------------------------------------

def recommend_model(
    n_samples: int,
    n_features: int,
    skip_dl: bool = False,
) -> dict[str, str]:
    """
    Analyse dataset properties and return a recommendation dict with
    reasoning for both the ML classifier/regressor and the DL model.

    Parameters
    ----------
    n_samples  : total number of labelled samples.
    n_features : number of input features.
    skip_dl    : whether DL training is disabled.

    Returns
    -------
    dict with keys: 'ml_clf', 'ml_reg', 'dl_model', 'reasoning'
    """
    ratio = n_features / max(n_samples, 1)

    # --- Classifier recommendation ----------------------------------------
    if n_samples < 100:
        ml_clf = "svm"
        clf_reason = (
            f"Very small dataset ({n_samples} samples). SVM with RBF kernel "
            "generalises well in low-sample, high-dimensional regimes and avoids "
            "overfitting that ensemble methods suffer from."
        )
    elif n_samples < 300:
        ml_clf = "random_forest"
        clf_reason = (
            f"Moderate dataset ({n_samples} samples). RandomForest provides "
            "good accuracy with built-in feature importance, handles mixed "
            "feature scales without heavy tuning, and is robust to outliers."
        )
    elif ratio > 1.5:
        ml_clf = "gradient_boosting"
        clf_reason = (
            f"High feature-to-sample ratio ({ratio:.2f}). "
            "GradientBoosting applies sequential regularisation and handles "
            "correlated spectral features better than plain RF in this regime."
        )
    else:
        ml_clf = "random_forest"
        clf_reason = (
            f"Large dataset ({n_samples} samples, ratio={ratio:.2f}). "
            "RandomForest is fast, parallelisable, and delivers near-optimal "
            "accuracy for tabular spectral data."
        )

    # --- Regressor recommendation -----------------------------------------
    if n_samples < 100:
        ml_reg = "ridge"
        reg_reason = (
            f"Very small dataset ({n_samples} samples). Ridge regression "
            "(L2-regularised linear model) prevents overfitting; "
            "ensemble regressors need more data to estimate variance reliably."
        )
    elif ratio > 2.0:
        ml_reg = "lasso"
        reg_reason = (
            f"More features than samples (ratio={ratio:.2f}). "
            "Lasso (L1 penalty) performs automatic feature selection, "
            "zeroing out uninformative spectral bins and improving generalisation."
        )
    elif n_samples < 300:
        ml_reg = "random_forest"
        reg_reason = (
            f"Moderate dataset ({n_samples} samples). RandomForestRegressor "
            "captures non-linear solvent/assay interactions without needing "
            "hyperparameter tuning of the learning rate."
        )
    else:
        ml_reg = "gradient_boosting"
        reg_reason = (
            f"Sufficient data ({n_samples} samples). GradientBoosting typically "
            "achieves the lowest MSE on structured/spectral regression tasks by "
            "iteratively correcting residuals."
        )

    # --- DL model recommendation ------------------------------------------
    if skip_dl:
        dl_model = "N/A (--skip-dl)"
        dl_reason = "DL training is disabled; no DL recommendation applies."
    elif n_samples < 150:
        dl_model = "mlp"
        dl_reason = (
            f"Small dataset ({n_samples} samples). The compact MLP (ANN) encoder "
            "is preferred: fewer parameters → less overfitting. "
            "CNN adds spatial inductive bias useful only when sample count is large "
            "enough to learn filters reliably (≥ ~300 per class)."
        )
    elif n_features > 200:
        dl_model = "cnn"
        dl_reason = (
            f"High-dimensional spectral input ({n_features} features). "
            "A 1-D CNN encoder extracts local spectral motifs (peaks, peak-clusters) "
            "via learned convolutional filters — this matches the structure of HPLC/GC-MS "
            "data where neighbouring RT/m·z bins are correlated. "
            "Use: python -m HPLC_GCMS_Fingerprint.run_pipeline --dl-model cnn"
        )
    else:
        dl_model = "mlp"
        dl_reason = (
            f"Balanced dataset ({n_samples} samples, {n_features} features). "
            "The MLP (ANN) shared encoder is a safe default: universal function "
            "approximator, fast to train, works well for multi-task regression+classification."
        )

    # --- Assemble output --------------------------------------------------
    reasoning = (
        "\n" + "=" * 64 + "\n"
        "  MODEL RECOMMENDATION  (based on your data properties)\n"
        + "=" * 64 + "\n"
        f"  Samples  : {n_samples}\n"
        f"  Features : {n_features}\n"
        f"  F/S ratio: {ratio:.2f}\n"
        + "-" * 64 + "\n"
        f"  ✔ ML Classifier  → {ml_clf}\n"
        f"    {clf_reason}\n\n"
        f"  ✔ ML Regressor   → {ml_reg}\n"
        f"    {reg_reason}\n\n"
        f"  ✔ DL Model       → {dl_model}\n"
        f"    {dl_reason}\n"
        + "-" * 64 + "\n"
        "  To switch models, re-run with:\n"
        "    --ml-clf  {random_forest|gradient_boosting|svm|knn|logistic_regression}\n"
        "    --ml-reg  {gradient_boosting|random_forest|ridge|lasso|svm|knn}\n"
        "    --dl-model {mlp|cnn}\n"
        + "=" * 64
    )

    return {
        "ml_clf":    ml_clf,
        "ml_reg":    ml_reg,
        "dl_model":  dl_model,
        "reasoning": reasoning,
    }
