from pathlib import Path
import pandas as pd
import numpy as np


def build_sample_id(df: pd.DataFrame) -> pd.Series:
    if "SampleID" in df.columns:
        return df["SampleID"].astype(str)
    return (
        df["Algal_Class"].astype(str)
        + "|"
        + df["Solvent"].astype(str)
        + "|"
        + df["Replicate"].astype(str)
    )


def load_omics(ms_file: Path) -> pd.DataFrame | None:
    if not ms_file or not Path(ms_file).exists():
        return None
    omics = pd.read_csv(ms_file)
    if "SampleID" not in omics.columns:
        raise ValueError("Omics file must contain a 'SampleID' column for alignment.")
    # Ensure features are numeric
    feature_cols = [c for c in omics.columns if c != "SampleID"]
    omics[feature_cols] = omics[feature_cols].apply(pd.to_numeric, errors="coerce")
    # Drop rows with all-NaN features
    omics = omics.dropna(subset=feature_cols, how="all")
    return omics


def merge_omics(meta_df: pd.DataFrame, omics_df: pd.DataFrame) -> pd.DataFrame:
    meta = meta_df.copy()
    meta["SampleID"] = build_sample_id(meta)
    merged = meta.merge(omics_df, on="SampleID", how="left")
    return merged


def reduce_omics(df: pd.DataFrame, n_components: int = 20):
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA

    feature_cols = [c for c in df.columns if c not in {
        "SampleID","Algal_Class","Solvent","Replicate","Extraction_Yield_mg_per_g",
        "Temperature_C","Incubation_h","FRAP","ABTS","DPPH","ORAC","TPC"
    }]
    if len(feature_cols) == 0:
        return df, []
    X = df[feature_cols].fillna(0.0).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    n_components = min(n_components, Xs.shape[1])
    pca = PCA(n_components=n_components, random_state=42)
    comps = pca.fit_transform(Xs)
    comp_cols = [f"omics_pca_{i+1}" for i in range(comps.shape[1])]
    df_out = df.copy()
    for i, col in enumerate(comp_cols):
        df_out[col] = comps[:, i]
    return df_out, comp_cols
