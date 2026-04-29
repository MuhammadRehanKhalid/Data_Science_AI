"""
Excel exporter: writes HPLC and GC-MS DataFrames to a multi-sheet workbook
together with a Solvent Properties sheet and a Data Dictionary.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import (
    ASSAYS,
    HPLC_RT_CENTERS,
    MZ_BIN_CENTERS,
    N_HPLC_PEAKS,
    N_MZ_BINS,
    SOLVENT_FULL_NAMES,
    SOLVENT_PROPS,
    SOLVENTS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _solvent_props_df() -> pd.DataFrame:
    """Build the Solvent Properties reference table."""
    rows = []
    for solvent in SOLVENTS:
        props = SOLVENT_PROPS[solvent]
        rows.append(
            {
                "solvent_code":       solvent,
                "full_name":          SOLVENT_FULL_NAMES[solvent],
                "polarity_index":     props["polarity_index"],
                "dielectric_constant": props["dielectric_constant"],
                "is_protic":          props["is_protic"],
                "notes": (
                    "Protic solvent – forms H-bonds with analytes"
                    if props["is_protic"]
                    else "Aprotic solvent – weaker H-bond donor"
                ),
            }
        )
    return pd.DataFrame(rows)


def _data_dictionary() -> pd.DataFrame:
    """Build the Data Dictionary sheet."""
    rows = []

    # ---- Shared metadata ----
    for col, dtype, unit, desc in [
        ("sample_id",  "string",  "—",          "Unique sample identifier (HPLC_XXXX or GCMS_XXXX)"),
        ("species",    "string",  "—",          "Algal species name"),
        ("phylum",     "string",  "—",          "Taxonomic phylum / class"),
        ("replicate",  "integer", "—",          "Replicate index (1 … n_replicates)"),
    ]:
        rows.append({"column": col, "dtype": dtype, "units": unit, "description": desc, "sheet": "HPLC_Fingerprints & GCMS_Fingerprints"})

    # ---- HPLC peak intensities ----
    for i in range(1, N_HPLC_PEAKS + 1):
        rows.append({
            "column":      f"intensity_RT_{i:02d}",
            "dtype":       "float",
            "units":       "AU (arbitrary units)",
            "description": f"Peak intensity at RT centre ≈ {HPLC_RT_CENTERS[i-1]:.2f} min",
            "sheet":       "HPLC_Fingerprints",
        })

    # ---- GC-MS m/z bin intensities ----
    for j in range(1, N_MZ_BINS + 1):
        rows.append({
            "column":      f"intensity_mz_{j:03d}",
            "dtype":       "float",
            "units":       "counts",
            "description": f"Summed ion intensity in m/z bin centred at ≈ {MZ_BIN_CENTERS[j-1]:.1f} Da",
            "sheet":       "GCMS_Fingerprints",
        })

    # ---- Per-solvent activity columns ----
    for solvent in SOLVENTS:
        rows.append({
            "column":      f"activity_{solvent}",
            "dtype":       "float",
            "units":       "0–100 (normalised)",
            "description": f"Mean antioxidant activity (DPPH+ABTS+FRAP)/3 with solvent {solvent}",
            "sheet":       "HPLC_Fingerprints & GCMS_Fingerprints",
        })
        for assay in ASSAYS:
            rows.append({
                "column":      f"{assay}_{solvent}",
                "dtype":       "float",
                "units":       "0–100",
                "description": f"{assay} radical-scavenging activity (%) using solvent {solvent}",
                "sheet":       "HPLC_Fingerprints & GCMS_Fingerprints",
            })

    # ---- Solvent properties sheet ----
    for col, dtype, unit, desc in [
        ("solvent_code",        "string",  "—",    "Short code used throughout the project"),
        ("full_name",           "string",  "—",    "Full solvent description"),
        ("polarity_index",      "float",   "—",    "Empirical polarity index (higher = more polar)"),
        ("dielectric_constant", "float",   "F/m",  "Relative permittivity at 25 °C"),
        ("is_protic",           "integer", "0/1",  "1 = protic, 0 = aprotic"),
    ]:
        rows.append({"column": col, "dtype": dtype, "units": unit, "description": desc, "sheet": "Solvent_Properties"})

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_to_excel(
    hplc_df: pd.DataFrame,
    gcms_df: pd.DataFrame,
    output_path: str | Path = "data/fingerprint_data.xlsx",
) -> Path:
    """
    Write HPLC and GC-MS DataFrames plus reference sheets to an Excel workbook.

    Parameters
    ----------
    hplc_df : pd.DataFrame
        Output of ``generate_hplc()``.
    gcms_df : pd.DataFrame
        Output of ``generate_gcms()``.
    output_path : str or Path
        Destination file path (will be created if needed).

    Returns
    -------
    Path
        Resolved path to the written workbook.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    solvent_props = _solvent_props_df()
    data_dict = _data_dictionary()

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        hplc_df.to_excel(writer, sheet_name="HPLC_Fingerprints",  index=False)
        gcms_df.to_excel(writer, sheet_name="GCMS_Fingerprints",  index=False)
        solvent_props.to_excel(writer, sheet_name="Solvent_Properties", index=False)
        data_dict.to_excel(writer, sheet_name="Data_Dictionary",  index=False)

    print(
        f"[ExcelExporter] Wrote {len(hplc_df)} HPLC rows and {len(gcms_df)} GC-MS rows "
        f"→ {output_path}"
    )
    return output_path
