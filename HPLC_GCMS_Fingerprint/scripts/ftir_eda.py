#!/usr/bin/env python3
"""Exploratory Data Analysis for FTIR outputs
Usage:
  python ftir_eda.py --processed_dir "HPLC_GCMS_Fingerprint/processed" --outdir "processed/eda"
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def basic_summary(processed_dir: Path, outdir: Path):
    processed_file = processed_dir / "ftir_all_processed.csv"
    binned_file = list(processed_dir.glob("ftir_binned_*.csv"))
    if not processed_file.exists():
        print("Processed file not found:", processed_file)
        return
    df = pd.read_csv(processed_file)
    outdir.mkdir(parents=True, exist_ok=True)

    # basic stats per sample
    stats = df.groupby('source_file')['A_norm'].describe()
    stats.to_csv(outdir / 'sample_stats.csv')

    # missing values
    missing = df.isna().sum()
    missing.to_frame('n_missing').to_csv(outdir / 'missing_values.csv')

    # distribution plot (violin) of A_norm by sample (top 20 samples)
    top_samples = df['source_file'].value_counts().index[:20]
    df_top = df[df['source_file'].isin(top_samples)]
    plt.figure(figsize=(10, 6))
    sns.violinplot(data=df_top, x='source_file', y='A_norm', inner='quartile')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(outdir / 'violin_A_norm_top20.png', dpi=150)
    plt.close()

    # if binned data exists, do correlation heatmap of first N bins
    if binned_file:
        bdf = pd.read_csv(binned_file[0])
        wide = bdf.pivot(index='source_file', columns='bin', values='bin_A').fillna(0)
        if wide.shape[1] >= 2:
            corr = wide.corr()
            plt.figure(figsize=(8, 6))
            sns.heatmap(corr, cmap='vlag', center=0)
            plt.tight_layout()
            plt.savefig(outdir / 'binned_correlation_heatmap.png', dpi=150)
            plt.close()

    print('EDA complete. Results in', outdir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--processed_dir', required=True)
    parser.add_argument('--outdir', required=False)
    args = parser.parse_args()
    p = Path(args.processed_dir)
    out = Path(args.outdir) if args.outdir else p / 'eda'
    basic_summary(p, out)


if __name__ == '__main__':
    main()
