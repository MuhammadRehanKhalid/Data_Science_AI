"""
Unified dataset object for multi-task HPLC / GC-MS modelling.

Usage
-----
    dataset = MultiTaskDataset.from_excel("data/fingerprint_data.xlsx")
    X_train, X_test, targets_train, targets_test = dataset.train_test_split()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .feature_engineering import build_feature_matrix, build_targets
from .loader import load_and_validate

# Imported to expose downstream
from ..data_generation.constants import ASSAYS, SOLVENTS


def _impute_non_finite_array(arr: np.ndarray, name: str) -> np.ndarray:
    """Replace NaN/inf values column-wise using finite medians (fallback: 0.0)."""
    out = np.asarray(arr, dtype=float).copy()
    if out.ndim != 2:
        return out

    finite_mask = np.isfinite(out)
    if finite_mask.all():
        return out

    n_bad = int((~finite_mask).sum())
    for j in range(out.shape[1]):
        col = out[:, j]
        good = np.isfinite(col)
        fill_value = float(np.median(col[good])) if np.any(good) else 0.0
        col[~good] = fill_value
        out[:, j] = col

    print(f"[Dataset] Imputed {n_bad} non-finite values in {name}.")
    return out


@dataclass
class MultiTaskDataset:
    """
    Container for the full multi-task feature and target arrays.

    Attributes
    ----------
    X : np.ndarray, shape (n_samples, n_features)
        Standardised feature matrix (combined representation by default).
    species : np.ndarray, shape (n_samples,)
        Integer species labels.
    phylum : np.ndarray, shape (n_samples,)
        Integer phylum labels.
    y_solvents : np.ndarray, shape (n_samples, n_solvents)
        Normalised antioxidant activity per solvent.
    y_assays : np.ndarray, shape (n_samples, n_assays)
        Normalised assay performance for the best solvent.
    best_solvent : np.ndarray of str, shape (n_samples,)
        Ground-truth best solvent per sample.
    best_assay : np.ndarray of str, shape (n_samples,)
        Ground-truth best assay per sample.
    species_names : list[str]
    phylum_names : list[str]
    solvent_names : list[str]
    assay_names : list[str]
    scaler : StandardScaler
        Fitted scaler (for inverse-transforming or reusing on new data).
    """

    X:             np.ndarray
    species:       np.ndarray
    phylum:        np.ndarray
    y_solvents:    np.ndarray
    y_assays:      np.ndarray
    best_solvent:  np.ndarray
    best_assay:    np.ndarray
    species_names: list[str]
    phylum_names:  list[str]
    solvent_names: list[str] = field(default_factory=list)
    assay_names:   list[str] = field(default_factory=list)
    scaler:        Optional[StandardScaler] = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_excel(
        cls,
        path: str | Path,
        representation: str = "combined",
        n_bins: int = 10,
        standardise: bool = True,
    ) -> "MultiTaskDataset":
        """
        Load workbook, engineer features, build targets, return dataset.

        Parameters
        ----------
        path : str or Path
        representation : str
            Feature representation passed to ``build_feature_matrix``.
        n_bins : int
            Bins for the 'binned' representation.
        standardise : bool
            Whether to apply ``StandardScaler`` to X.
        """
        # Load whatever sheets are present (HPLC, GCMS, optional)
        from .loader import load_and_validate_optional

        hplc_df, gcms_df, solvent_df = load_and_validate_optional(path)

        # Build feature matrix from available sources (FTIR not expected in workbook)
        X = build_feature_matrix(
            hplc_df=hplc_df,
            gcms_df=gcms_df,
            ftir_df=None,
            representation=representation,
            n_bins=n_bins,
        )

        # Determine which sheet to use for targets: prefer HPLC, fallback to GCMS
        target_df = hplc_df if hplc_df is not None else gcms_df
        if target_df is None:
            raise ValueError(
                "No HPLC or GC-MS sheet available in workbook to extract targets from."
            )

        targets = build_targets(target_df, solvents=SOLVENTS, assays=ASSAYS)

        X = _impute_non_finite_array(X, name="feature matrix")
        targets["y_solvents"] = _impute_non_finite_array(targets["y_solvents"], name="solvent targets")
        targets["y_assays"] = _impute_non_finite_array(targets["y_assays"], name="assay targets")

        scaler = None
        if standardise:
            scaler = StandardScaler()
            X = scaler.fit_transform(X)

        return cls(
            X             = X,
            species       = targets["species"],
            phylum        = targets["phylum"],
            y_solvents    = targets["y_solvents"],
            y_assays      = targets["y_assays"],
            best_solvent  = targets["best_solvent"],
            best_assay    = targets["best_assay"],
            species_names = targets["species_names"],
            phylum_names  = targets["phylum_names"],
            solvent_names = SOLVENTS,
            assay_names   = ASSAYS,
            scaler        = scaler,
        )

    @classmethod
    def from_sources(
        cls,
        hplc_df: pd.DataFrame | None = None,
        gcms_df: pd.DataFrame | None = None,
        ftir_df: pd.DataFrame | None = None,
        representation: str = "combined",
        n_bins: int = 10,
        standardise: bool = True,
    ) -> "MultiTaskDataset":
        """
        Build a dataset directly from provided DataFrames. Any combination
        of HPLC, GCMS and FTIR may be supplied. Targets are extracted from
        HPLC if available, otherwise GCMS, otherwise FTIR (if it contains
        the expected target columns).
        """
        def _align_frames(
            frames: list[pd.DataFrame | None],
        ) -> tuple[pd.DataFrame | None, ...]:
            present = [df for df in frames if df is not None]
            if not present:
                return tuple(frames)

            # Prefer alignment on sample_id when all sources expose it.
            if all("sample_id" in df.columns for df in present):
                common_ids = set(present[0]["sample_id"].astype(str))
                for df in present[1:]:
                    common_ids &= set(df["sample_id"].astype(str))
                common_ids = sorted(common_ids)
                if common_ids:
                    aligned: list[pd.DataFrame | None] = []
                    for df in frames:
                        if df is None:
                            aligned.append(None)
                        else:
                            aligned.append(
                                df.assign(sample_id=df["sample_id"].astype(str)).set_index("sample_id").loc[common_ids].reset_index()
                            )
                    return tuple(aligned)

            # Fallback: trim all sources to the smallest shared row count.
            min_len = min(len(df) for df in present)
            return tuple(None if df is None else df.iloc[:min_len].reset_index(drop=True) for df in frames)

        hplc_df, gcms_df, ftir_df = _align_frames([hplc_df, gcms_df, ftir_df])

        X = build_feature_matrix(
            hplc_df=hplc_df,
            gcms_df=gcms_df,
            ftir_df=ftir_df,
            representation=representation,
            n_bins=n_bins,
        )

        # Choose a source that contains target/activity columns
        target_df = None
        for candidate in (hplc_df, gcms_df, ftir_df):
            if candidate is None:
                continue
            # Check for an activity column as heuristic
            if any(c.startswith("activity_") for c in candidate.columns):
                target_df = candidate
                break

        if target_df is None:
            raise ValueError(
                "No suitable source with target/activity columns found. "
                "Provide HPLC or GCMS (or FTIR with activity columns) to extract targets."
            )

        targets = build_targets(target_df, solvents=SOLVENTS, assays=ASSAYS)

        X = _impute_non_finite_array(X, name="feature matrix")
        targets["y_solvents"] = _impute_non_finite_array(targets["y_solvents"], name="solvent targets")
        targets["y_assays"] = _impute_non_finite_array(targets["y_assays"], name="assay targets")

        scaler = None
        if standardise:
            scaler = StandardScaler()
            X = scaler.fit_transform(X)

        return cls(
            X             = X,
            species       = targets["species"],
            phylum        = targets["phylum"],
            y_solvents    = targets["y_solvents"],
            y_assays      = targets["y_assays"],
            best_solvent  = targets["best_solvent"],
            best_assay    = targets["best_assay"],
            species_names = targets["species_names"],
            phylum_names  = targets["phylum_names"],
            solvent_names = SOLVENTS,
            assay_names   = ASSAYS,
            scaler        = scaler,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def train_test_split(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> tuple["MultiTaskDataset", "MultiTaskDataset"]:
        """
        Return (train_dataset, test_dataset) with stratification on species.
        """
        idx = np.arange(len(self.X))
        # Stratification requires at least 2 samples per class and enough room
        # for the requested split. Fall back to an unstratified split when the
        # dataset is too small for that constraint.
        unique_species, species_counts = np.unique(self.species, return_counts=True)
        can_stratify = (
            len(unique_species) > 1
            and species_counts.min() >= 2
            and int(np.ceil(len(self.X) * test_size)) >= len(unique_species)
            and int(np.floor(len(self.X) * (1.0 - test_size))) >= len(unique_species)
        )
        tr_idx, te_idx = train_test_split(
            idx,
            test_size=test_size,
            random_state=random_state,
            stratify=self.species if can_stratify else None,
        )
        return self._subset(tr_idx), self._subset(te_idx)

    def _subset(self, idx: np.ndarray) -> "MultiTaskDataset":
        return MultiTaskDataset(
            X             = self.X[idx],
            species       = self.species[idx],
            phylum        = self.phylum[idx],
            y_solvents    = self.y_solvents[idx],
            y_assays      = self.y_assays[idx],
            best_solvent  = self.best_solvent[idx],
            best_assay    = self.best_assay[idx],
            species_names = self.species_names,
            phylum_names  = self.phylum_names,
            solvent_names = self.solvent_names,
            assay_names   = self.assay_names,
            scaler        = self.scaler,
        )

    def __len__(self) -> int:
        return len(self.X)

    def __repr__(self) -> str:
        return (
            f"MultiTaskDataset("
            f"n_samples={len(self)}, "
            f"n_features={self.X.shape[1]}, "
            f"n_species={len(self.species_names)}, "
            f"n_solvents={len(self.solvent_names)}, "
            f"n_assays={len(self.assay_names)})"
        )
