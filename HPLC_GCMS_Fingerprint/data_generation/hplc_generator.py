"""
HPLC fingerprint dummy-data generator.

Produces a DataFrame with:
- One row per (species × replicate).
- 50 RT peak-intensity columns (intensity_RT_01 … intensity_RT_50).
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
    HPLC_RT_CENTERS,
    N_HPLC_PEAKS,
    PHYLA,
    SOLVENT_PROPS,
    SOLVENTS,
    SPECIES,
    SPECIES_BASELINE,
)


def _sim_peak_intensities(
    baseline: float,
    polarity_norm: float,
    rng: np.random.Generator,
    n_peaks: int = N_HPLC_PEAKS,
) -> np.ndarray:
    """
    Simulate HPLC peak intensities for one solvent extraction.
    Returns array of shape (n_peaks,).
    """
    scale = baseline * (0.4 + 0.6 * polarity_norm)
    intensities = rng.exponential(scale=scale * 1e5, size=n_peaks)
    # Some peaks absent depending on polarity
    presence_prob = 0.25 + 0.5 * polarity_norm
    mask = rng.random(n_peaks) < presence_prob
    return intensities * mask.astype(float)


def _sim_assay_scores(
    baseline: float,
    polarity_norm: float,
    rng: np.random.Generator,
) -> dict[str, float]:
    """
    Simulate DPPH / ABTS / FRAP scores (0-100) correlated with species
    antioxidant content and solvent polarity.
    """
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


def generate_hplc(
    n_replicates: int = 15,
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic HPLC peak-table data.

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
        Columns: metadata + HPLC peak intensities + per-solvent activity scores.
    """
    rng = np.random.default_rng(random_seed)
    rows: list[dict] = []
    sample_counter = 0

    for sp in SPECIES:
        baseline = SPECIES_BASELINE[sp]
        phylum = PHYLA[sp]

        for rep in range(1, n_replicates + 1):
            sample_counter += 1
            sample_id = f"HPLC_{sample_counter:04d}"

            # Fingerprint: use standard methanol extraction as the "reference"
            polarity_ref = SOLVENT_PROPS["MeOH_70"]["polarity_index"] / 10.2
            intensities = _sim_peak_intensities(baseline, polarity_ref, rng)

            # Per-solvent antioxidant activity
            solvent_rows: dict[str, dict[str, float]] = {}
            for solvent in SOLVENTS:
                pol = SOLVENT_PROPS[solvent]["polarity_index"] / 10.2
                solvent_rows[solvent] = _sim_assay_scores(baseline, pol, rng)

            row: dict = {
                "sample_id":  sample_id,
                "species":    sp,
                "phylum":     phylum,
                "replicate":  rep,
            }

            # HPLC peak intensities at fixed RT positions
            for i in range(N_HPLC_PEAKS):
                row[f"intensity_RT_{i+1:02d}"] = float(intensities[i])

            # Per-solvent combined activity score (mean of DPPH+ABTS+FRAP)
            for solvent in SOLVENTS:
                assay_vals = solvent_rows[solvent]
                row[f"activity_{solvent}"] = float(
                    np.mean([assay_vals[a] for a in ASSAYS])
                )
                for assay in ASSAYS:
                    row[f"{assay}_{solvent}"] = assay_vals[assay]

            rows.append(row)

    return pd.DataFrame(rows)
