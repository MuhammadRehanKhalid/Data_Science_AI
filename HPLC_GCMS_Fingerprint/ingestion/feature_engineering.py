"""
Feature engineering for HPLC and GC-MS fingerprint DataFrames.

Supported representations
--------------------------
raw        : log-normalised peak intensities (HPLC or GC-MS).
binned     : intensities summed into coarser RT / m/z bins.
binary     : presence/absence indicator (1 if intensity > threshold).
meta       : derived statistical meta-features per sample.
combined   : concatenation of raw + binned + binary + meta for both modalities.

All functions accept a cleaned DataFrame (output of ``loader.validate_schema``)
and return a NumPy array of shape (n_samples, n_features).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import skew


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _intensity_cols(df: pd.DataFrame, prefix: str) -> list[str]:
    """Return sorted column names that start with *prefix*."""
    return sorted([c for c in df.columns if c.startswith(prefix)])


def _log_normalise(arr: np.ndarray) -> np.ndarray:
    """log1p normalisation; keeps shape."""
    return np.log1p(arr)


# ---------------------------------------------------------------------------
# Single-modality feature builders
# ---------------------------------------------------------------------------

def raw_features(df: pd.DataFrame, intensity_prefix: str) -> np.ndarray:
    """
    Log-normalised raw peak intensities.

    Returns shape (n_samples, n_peaks).
    """
    cols = _intensity_cols(df, intensity_prefix)
    arr = df[cols].to_numpy(dtype=float)
    return _log_normalise(arr)


def binned_features(
    df: pd.DataFrame,
    intensity_prefix: str,
    n_bins: int = 10,
) -> np.ndarray:
    """
    Divide peaks into *n_bins* equally sized groups and sum intensities.

    Returns shape (n_samples, n_bins).
    """
    cols = _intensity_cols(df, intensity_prefix)
    arr = df[cols].to_numpy(dtype=float)
    n_peaks = arr.shape[1]
    bin_edges = np.array_split(np.arange(n_peaks), n_bins)
    binned = np.column_stack([arr[:, idx].sum(axis=1) for idx in bin_edges])
    return _log_normalise(binned)


def binary_features(
    df: pd.DataFrame,
    intensity_prefix: str,
    threshold: float = 0.0,
) -> np.ndarray:
    """
    Binary presence/absence fingerprint: 1 if intensity > threshold.

    Returns shape (n_samples, n_peaks).
    """
    cols = _intensity_cols(df, intensity_prefix)
    arr = df[cols].to_numpy(dtype=float)
    return (arr > threshold).astype(float)


def meta_features(df: pd.DataFrame, intensity_prefix: str) -> np.ndarray:
    """
    Derived statistical meta-features per sample:
    [mean, std, n_present, skewness, max_intensity, peak_diversity_ratio].

    Returns shape (n_samples, 6).
    """
    cols = _intensity_cols(df, intensity_prefix)
    arr = df[cols].to_numpy(dtype=float)

    mean_int  = arr.mean(axis=1, keepdims=True)
    std_int   = arr.std(axis=1, keepdims=True)
    n_present = (arr > 0).sum(axis=1, keepdims=True).astype(float)
    skewness  = np.apply_along_axis(
        lambda x: skew(x) if x.std() > 0 else 0.0, 1, arr
    ).reshape(-1, 1)
    max_int   = arr.max(axis=1, keepdims=True)
    diversity = n_present / arr.shape[1]   # fraction of peaks present

    return np.hstack([
        _log_normalise(mean_int),
        _log_normalise(std_int + 1e-9),
        _log_normalise(n_present + 1),
        skewness,
        _log_normalise(max_int),
        diversity,
    ])


# ---------------------------------------------------------------------------
# Combined feature builder
# ---------------------------------------------------------------------------

def build_feature_matrix(
    hplc_df: pd.DataFrame,
    gcms_df: pd.DataFrame,
    representation: str = "combined",
    n_bins: int = 10,
) -> np.ndarray:
    """
    Build the feature matrix used for modelling.

    Parameters
    ----------
    hplc_df : pd.DataFrame
        Validated HPLC fingerprint DataFrame (n_samples rows).
    gcms_df : pd.DataFrame
        Validated GC-MS fingerprint DataFrame (n_samples rows, same order).
    representation : str
        One of 'raw', 'binned', 'binary', 'meta', 'combined'.
    n_bins : int
        Number of bins for 'binned' representation.

    Returns
    -------
    np.ndarray of shape (n_samples, n_features).
    """
    hplc_prefix = "intensity_RT_"
    gcms_prefix = "intensity_mz_"

    builders = {
        "raw":    lambda: np.hstack([
            raw_features(hplc_df, hplc_prefix),
            raw_features(gcms_df, gcms_prefix),
        ]),
        "binned": lambda: np.hstack([
            binned_features(hplc_df, hplc_prefix, n_bins=n_bins),
            binned_features(gcms_df, gcms_prefix, n_bins=n_bins),
        ]),
        "binary": lambda: np.hstack([
            binary_features(hplc_df, hplc_prefix),
            binary_features(gcms_df, gcms_prefix),
        ]),
        "meta":   lambda: np.hstack([
            meta_features(hplc_df, hplc_prefix),
            meta_features(gcms_df, gcms_prefix),
        ]),
        "combined": lambda: np.hstack([
            raw_features(hplc_df,    hplc_prefix),
            raw_features(gcms_df,    gcms_prefix),
            binned_features(hplc_df, hplc_prefix, n_bins=n_bins),
            binned_features(gcms_df, gcms_prefix, n_bins=n_bins),
            binary_features(hplc_df, hplc_prefix),
            binary_features(gcms_df, gcms_prefix),
            meta_features(hplc_df,   hplc_prefix),
            meta_features(gcms_df,   gcms_prefix),
        ]),
    }

    if representation not in builders:
        raise ValueError(
            f"Unknown representation '{representation}'. "
            f"Choose from: {list(builders.keys())}"
        )

    X = builders[representation]()
    print(
        f"[FeatureEngineering] representation='{representation}' → "
        f"X.shape={X.shape}"
    )
    return X


# ---------------------------------------------------------------------------
# Target builders
# ---------------------------------------------------------------------------

def build_targets(
    df: pd.DataFrame,
    solvents: list[str],
    assays: list[str],
) -> dict[str, np.ndarray]:
    """
    Extract multi-task target arrays from a fingerprint DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Either hplc_df or gcms_df (same structure).
    solvents : list[str]
        Ordered list of solvent codes matching column suffixes.
    assays : list[str]
        Ordered list of assay names matching column prefixes.

    Returns
    -------
    dict with keys:
        'species'      : int array (n_samples,)  – encoded species labels
        'phylum'       : int array (n_samples,)  – encoded phylum labels
        'y_solvents'   : float array (n_samples, n_solvents) – activity
        'y_assays'     : float array (n_samples, n_assays)   – best-solvent assay scores
        'best_solvent' : str array  (n_samples,)
        'best_assay'   : str array  (n_samples,)
        'species_names': list[str] – sorted unique species labels
        'phylum_names' : list[str] – sorted unique phylum labels
    """
    # Integer-encode categorical targets
    species_names = sorted(df["species"].unique().tolist())
    phylum_names  = sorted(df["phylum"].unique().tolist())
    species_enc   = df["species"].map({s: i for i, s in enumerate(species_names)}).to_numpy()
    phylum_enc    = df["phylum"].map({p: i for i, p in enumerate(phylum_names)}).to_numpy()

    # Solvent activity matrix  (n_samples × n_solvents)
    y_solvents = df[[f"activity_{s}" for s in solvents]].to_numpy(dtype=float)
    # Normalise to [0, 1]
    sol_min, sol_max = y_solvents.min(), y_solvents.max()
    if sol_max > sol_min:
        y_solvents = (y_solvents - sol_min) / (sol_max - sol_min)

    # Best solvent per sample
    best_solvent_idx = y_solvents.argmax(axis=1)
    best_solvent_arr = np.array([solvents[i] for i in best_solvent_idx])

    # Assay score matrix for the best solvent (n_samples × n_assays)
    y_assays = np.zeros((len(df), len(assays)), dtype=float)
    for row_i, best_sol in enumerate(best_solvent_arr):
        for col_j, assay in enumerate(assays):
            y_assays[row_i, col_j] = df.iloc[row_i][f"{assay}_{best_sol}"]
    # Normalise to [0, 1]
    ass_min, ass_max = y_assays.min(), y_assays.max()
    if ass_max > ass_min:
        y_assays = (y_assays - ass_min) / (ass_max - ass_min)

    best_assay_idx = y_assays.argmax(axis=1)
    best_assay_arr = np.array([assays[i] for i in best_assay_idx])

    return {
        "species":       species_enc,
        "phylum":        phylum_enc,
        "y_solvents":    y_solvents,
        "y_assays":      y_assays,
        "best_solvent":  best_solvent_arr,
        "best_assay":    best_assay_arr,
        "species_names": species_names,
        "phylum_names":  phylum_names,
    }
