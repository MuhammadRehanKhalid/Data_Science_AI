"""
GC-MS fingerprint dummy-data generator.

Produces a DataFrame with:
- One row per (species × replicate).
- 80 m/z bin-intensity columns (intensity_mz_001 … intensity_mz_080).
- Antioxidant activity per solvent columns (activity_<solvent>) – combined score.
- Per-solvent/per-assay values (DPPH_<solvent>, ABTS_<solvent>, FRAP_<solvent>).
- Metadata: sample_id, species, phylum, replicate.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import (
    ASSAY_BASE_INTERCEPT,
    ASSAY_POLARITY_WEIGHT,
    ASSAYS,
    MZ_BIN_CENTERS,
    N_MZ_BINS,
    PHYLA,
    SOLVENT_PROPS,
    SOLVENTS,
    SPECIES,
    SPECIES_BASELINE,
)


def _sim_mz_intensities(
    baseline: float,
    polarity_norm: float,
    rng: np.random.Generator,
    n_bins: int = N_MZ_BINS,
) -> np.ndarray:
    """
    Simulate GC-MS m/z bin intensities for one solvent extraction.
    Returns array of shape (n_bins,).
    """
    scale = baseline * (0.35 + 0.65 * polarity_norm)
    intensities = rng.exponential(scale=scale * 1e6, size=n_bins)
    # Non-polar solvents extract different compounds → more peaks at higher m/z
    high_mz_boost = (MZ_BIN_CENTERS / MZ_BIN_CENTERS.max()) * (1.0 - polarity_norm)
    intensities *= (1.0 + high_mz_boost)
    # Random presence / absence
    presence_prob = 0.20 + 0.45 * polarity_norm
    mask = rng.random(n_bins) < presence_prob
    return intensities * mask.astype(float)


def _sim_assay_scores(
    baseline: float,
    polarity_norm: float,
    rng: np.random.Generator,
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for assay in ASSAYS:
        noise = rng.normal(0.0, 0.04)
        raw = 100.0 * (
            ASSAY_BASE_INTERCEPT[assay]
            + ASSAY_POLARITY_WEIGHT[assay] * baseline * polarity_norm
            + noise
        )
        scores[assay] = float(np.clip(raw, 0.0, 100.0))
    return scores


def generate_gcms(
    n_replicates: int = 15,
    random_seed: int = 43,
) -> pd.DataFrame:
    """
    Generate synthetic GC-MS m/z-bin-intensity data.

    Parameters
    ----------
    n_replicates : int
        Biological/technical replicates per species.
    random_seed : int
        Seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Rows = samples (species × replicate).
        Columns: metadata + GC-MS m/z bin intensities + per-solvent activity.
    """
    rng = np.random.default_rng(random_seed)
    rows: list[dict] = []
    sample_counter = 0

    for sp in SPECIES:
        baseline = SPECIES_BASELINE[sp]
        phylum = PHYLA[sp]

        for rep in range(1, n_replicates + 1):
            sample_counter += 1
            sample_id = f"GCMS_{sample_counter:04d}"

            # Fingerprint via methanol reference extraction
            polarity_ref = SOLVENT_PROPS["MeOH_70"]["polarity_index"] / 10.2
            intensities = _sim_mz_intensities(baseline, polarity_ref, rng)

            # Per-solvent antioxidant activity
            solvent_scores: dict[str, dict[str, float]] = {}
            for solvent in SOLVENTS:
                pol = SOLVENT_PROPS[solvent]["polarity_index"] / 10.2
                solvent_scores[solvent] = _sim_assay_scores(baseline, pol, rng)

            row: dict = {
                "sample_id":  sample_id,
                "species":    sp,
                "phylum":     phylum,
                "replicate":  rep,
            }

            # GC-MS m/z bin intensities
            for j in range(N_MZ_BINS):
                row[f"intensity_mz_{j+1:03d}"] = float(intensities[j])

            # Per-solvent combined activity + individual assay values
            for solvent in SOLVENTS:
                assay_vals = solvent_scores[solvent]
                row[f"activity_{solvent}"] = float(
                    np.mean([assay_vals[a] for a in ASSAYS])
                )
                for assay in ASSAYS:
                    row[f"{assay}_{solvent}"] = assay_vals[assay]

            rows.append(row)

    return pd.DataFrame(rows)
