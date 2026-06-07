#!/usr/bin/env python3
"""FTIR merge & preprocessing pipeline
Usage:
  python ftir_merge_pipeline.py --input_dir "path/to/csvs" --output_dir "processed" --bin_width 5 --norm minsub --do_pca
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA


def find_numeric_columns(df):
    nums = df.select_dtypes(include=[np.number]).columns.tolist()
    return nums[:2] if len(nums) >= 2 else []


def read_spectrum(path: Path, skip: int = 1):
    df = pd.read_csv(path, skiprows=skip)
    numcols = find_numeric_columns(df)
    if not numcols:
        raise ValueError(f"No numeric columns found in {path}")
    df2 = df.loc[:, numcols[:2]].copy()
    df2.columns = ["cm.1", "A"]
    return df2


def save_plots_overlay_and_facet(df_all_raw: pd.DataFrame, outdir: Path):
    plt.figure(figsize=(9, 6))
    sns.lineplot(data=df_all_raw, x="cm.1", y="A", hue="source_file", linewidth=0.8)
    plt.gca().invert_xaxis()
    plt.xlabel("Wavenumber (cm^-1)")
    plt.ylabel("Absorbance")
    plt.tight_layout()
    plt.savefig(outdir / "spectra_overlay_raw.png", dpi=150)
    plt.close()

    # facet
    unique = df_all_raw["source_file"].nunique()
    height = max(3, 0.15 * unique + 2)
    g = sns.FacetGrid(df_all_raw, col="source_file", col_wrap=1, sharey=False, height=1.2)
    g.map_dataframe(sns.lineplot, x="cm.1", y="A", color="steelblue")
    for ax in g.axes.flat:
        ax.invert_xaxis()
    plt.savefig(outdir / "spectra_facet_raw.png", dpi=150, bbox_inches="tight")
    plt.close()


def preprocess(df_all_raw: pd.DataFrame, norm: str):
    df = df_all_raw.copy()
    df["A_minsub"] = df.groupby("source_file")["A"].transform(lambda x: x - x.min())
    df["A_minsub"] = df["A_minsub"].clip(lower=0)

    if norm == "minmax":
        df["A_norm"] = df.groupby("source_file")["A"].transform(lambda x: (x - x.min()) / (x.max() - x.min()))
    elif norm == "zscore":
        df["A_norm"] = df.groupby("source_file")["A"].transform(lambda x: (x - x.mean()) / x.std(ddof=0))
    elif norm == "minsub":
        df["A_norm"] = df["A_minsub"]
    elif norm == "none":
        df["A_norm"] = df["A"]
    else:
        raise ValueError("Unknown normalization method")
    return df


def bin_wavenumbers(df: pd.DataFrame, bin_width: float):
    cm_min = np.floor(df["cm.1"].min())
    cm_max = np.ceil(df["cm.1"].max())
    bins = np.arange(cm_min, cm_max + bin_width, bin_width)
    df = df.copy()
    df["bin"] = pd.cut(df["cm.1"], bins=bins, include_lowest=True, right=False)
    binned = df.groupby(["source_file", "bin"]).agg(bin_cm=("cm.1", "mean"), bin_A=("A_norm", "mean")).reset_index()
    return binned


def detect_peaks(df: pd.DataFrame):
    out = []
    for name, g in df.groupby("source_file"):
        arr = g.sort_values("cm.1", ascending=False)["A_norm"].values
        cms = g.sort_values("cm.1", ascending=False)["cm.1"].values
        if len(arr) < 3:
            continue
        peaks_idx = np.where((arr[1:-1] > arr[:-2]) & (arr[1:-1] > arr[2:]))[0] + 1
        for i in peaks_idx:
            out.append({"source_file": name, "cm.1": cms[i], "A_norm": arr[i]})
    return pd.DataFrame(out)


def run_pca_on_binned(binned: pd.DataFrame, outdir: Path):
    wide = binned.pivot(index="source_file", columns="bin", values="bin_A").fillna(0)
    pca = PCA(n_components=min(10, wide.shape[1]))
    scores = pca.fit_transform(wide.values)
    pcs = pd.DataFrame(scores, index=wide.index, columns=[f"PC{i+1}" for i in range(scores.shape[1])])
    pcs.to_csv(outdir / "pca_scores.csv")
    var = pca.explained_variance_ratio_
    scree = pd.DataFrame({"PC": [f"PC{i+1}" for i in range(len(var))], "Variance": var})
    scree.to_csv(outdir / "pca_scree.csv", index=False)
    # plots
    plt.figure(figsize=(6, 4))
    sns.barplot(x="PC", y="Variance", data=scree, color="steelblue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(outdir / "pca_scree.png", dpi=150)
    plt.close()
    if pcs.shape[1] >= 2:
        plt.figure(figsize=(6, 5))
        sns.scatterplot(x=pcs["PC1"], y=pcs["PC2"])
        for i, txt in enumerate(pcs.index):
            plt.text(pcs["PC1"].iat[i], pcs["PC2"].iat[i], txt, fontsize=8)
        plt.tight_layout()
        plt.savefig(outdir / "pca_scores.png", dpi=150)
        plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=False)
    parser.add_argument("--skip_lines", type=int, default=1)
    parser.add_argument("--bin_width", type=float, default=5.0)
    parser.add_argument("--norm", choices=["minsub", "minmax", "zscore", "none"], default="minsub")
    parser.add_argument("--do_pca", action="store_true")
    parser.add_argument("--pattern", default=".csv")
    args = parser.parse_args()

    inp = Path(args.input_dir)
    outdir = Path(args.output_dir) if args.output_dir else Path(inp) / "processed"
    outdir.mkdir(parents=True, exist_ok=True)

    files = list(inp.glob(f"*{args.pattern}"))
    if not files:
        print("No files found in input_dir")
        return

    rows = []
    for f in files:
        try:
            df = read_spectrum(f, skip=args.skip_lines)
        except Exception as e:
            print(f"Skipping {f}: {e}")
            continue
        df["source_file"] = f.name
        rows.append(df)

    df_all_raw = pd.concat(rows, ignore_index=True)
    df_all_raw = df_all_raw[["source_file", "cm.1", "A"]]
    df_all_raw.to_csv(outdir / "ftir_all_raw.csv", index=False)

    df_wide_raw = df_all_raw.pivot(index="cm.1", columns="source_file", values="A")
    df_wide_raw.to_csv(outdir / "ftir_wide_raw.csv")

    save_plots_overlay_and_facet(df_all_raw, outdir)

    df_processed = preprocess(df_all_raw, args.norm)
    df_processed.to_csv(outdir / "ftir_all_processed.csv", index=False)

    binned = bin_wavenumbers(df_processed, args.bin_width)
    binned.to_csv(outdir / f"ftir_binned_{int(args.bin_width)}cm-1.csv", index=False)

    hist_dir = outdir / "histograms"
    hist_dir.mkdir(exist_ok=True)
    for name, g in binned.groupby("source_file"):
        plt.figure(figsize=(6, 4))
        sns.histplot(g["bin_A"].dropna(), bins=40, color="steelblue")
        plt.tight_layout()
        plt.savefig(hist_dir / f"{name}_hist.png", dpi=150)
        plt.close()

    peaks = detect_peaks(df_processed)
    peaks.to_csv(outdir / "ftir_peaks.csv", index=False)

    if args.do_pca:
        run_pca_on_binned(binned, outdir)

    print("Processing complete. Outputs written to:", outdir)


if __name__ == "__main__":
    main()
