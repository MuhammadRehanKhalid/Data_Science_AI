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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .feature_engineering import build_feature_matrix, build_targets
from .loader import load_and_validate

# Imported to expose downstream
from ..data_generation.constants import ASSAYS, SOLVENTS


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
        hplc_df, gcms_df, _ = load_and_validate(path)

        # Align rows (samples should be identical between sheets)
        if len(hplc_df) != len(gcms_df):
            raise ValueError(
                f"HPLC ({len(hplc_df)}) and GC-MS ({len(gcms_df)}) "
                "sheets have different row counts."
            )

        X = build_feature_matrix(hplc_df, gcms_df, representation=representation, n_bins=n_bins)

        # Use HPLC sheet for targets (both sheets carry identical target cols)
        targets = build_targets(hplc_df, solvents=SOLVENTS, assays=ASSAYS)

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
        tr_idx, te_idx = train_test_split(
            idx,
            test_size=test_size,
            random_state=random_state,
            stratify=self.species,
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
