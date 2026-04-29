"""
Excel data loader and schema validator.

Reads the workbook written by ``excel_exporter.py`` and returns validated
DataFrames ready for feature engineering.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

# Expected sheets
HPLC_SHEET = "HPLC_Fingerprints"
GCMS_SHEET = "GCMS_Fingerprints"
SOLVENT_SHEET = "Solvent_Properties"

# Columns that must exist in fingerprint sheets
_META_COLS = ["sample_id", "species", "phylum", "replicate"]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def load_workbook(
    path: str | Path,
) -> dict[str, pd.DataFrame]:
    """
    Load all sheets from the fingerprint workbook.

    Parameters
    ----------
    path : str or Path
        Path to the Excel workbook.

    Returns
    -------
    dict mapping sheet name → DataFrame.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Workbook not found: {path}")

    sheets = pd.read_excel(path, sheet_name=None)  # load all sheets
    return sheets


def validate_schema(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """
    Validate that required metadata columns exist and apply basic
    cleaning (strip whitespace, coerce numerics, fill NaN).

    Parameters
    ----------
    df : pd.DataFrame
        Raw sheet DataFrame.
    sheet_name : str
        Human-readable name for error messages.

    Returns
    -------
    Cleaned DataFrame.
    """
    missing = [c for c in _META_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            f"[{sheet_name}] Missing required columns: {missing}"
        )

    # Strip whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # Coerce numeric columns; warn about any NaN introduced
    num_cols = [c for c in df.columns if c not in _META_COLS]
    for col in num_cols:
        original_na = df[col].isna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        new_na = df[col].isna().sum() - original_na
        if new_na > 0:
            warnings.warn(
                f"[{sheet_name}] Column '{col}': {new_na} non-numeric "
                "values coerced to NaN.",
                stacklevel=2,
            )

    # Handle missing values: fill with column median for numeric columns
    numeric_df = df.select_dtypes(include="number")
    na_counts = numeric_df.isna().sum()
    filled_cols = na_counts[na_counts > 0]
    if not filled_cols.empty:
        warnings.warn(
            f"[{sheet_name}] Filling {filled_cols.sum()} NaN values with "
            "column medians.",
            stacklevel=2,
        )
        for col in filled_cols.index:
            df[col] = df[col].fillna(df[col].median())

    return df


def load_and_validate(
    path: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the workbook and return (hplc_df, gcms_df, solvent_props_df).

    All DataFrames are schema-validated and cleaned.
    """
    sheets = load_workbook(path)

    for name in (HPLC_SHEET, GCMS_SHEET, SOLVENT_SHEET):
        if name not in sheets:
            raise ValueError(
                f"Required sheet '{name}' not found in workbook. "
                f"Available sheets: {list(sheets.keys())}"
            )

    hplc_df   = validate_schema(sheets[HPLC_SHEET].copy(), HPLC_SHEET)
    gcms_df   = validate_schema(sheets[GCMS_SHEET].copy(), GCMS_SHEET)
    solvent_df = sheets[SOLVENT_SHEET].copy()

    print(
        f"[Loader] Loaded {len(hplc_df)} HPLC samples, "
        f"{len(gcms_df)} GC-MS samples."
    )
    return hplc_df, gcms_df, solvent_df
