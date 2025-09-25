"""
main.py -- run this to regenerate the dummy data and plots for step 1 (Nanodrop + Spectrometer)
"""
from pathlib import Path
import pandas as pd
from generate_data import generate_nanodrop_samples, generate_uvvis, generate_eem
from plot_graphs import plot_nanodrop, plot_uvvis, plot_eem

root = Path(__file__).resolve().parents[1]
data_dir = root / "data"
plots_dir = root / "plots"

df_nanodrop_long, df_nanodrop_summary = generate_nanodrop_samples()
df_nanodrop_long.to_csv(data_dir / "nanodrop_spectra_long.csv", index=False)
df_nanodrop_summary.to_csv(data_dir / "nanodrop_summary.csv", index=False)
plot_nanodrop(df_nanodrop_long, plots_dir / "nanodrop_spectra.png")

df_uvvis = generate_uvvis()
df_uvvis.to_csv(data_dir / "uvvis_spectra_long.csv", index=False)
plot_uvvis(df_uvvis, plots_dir / "uvvis_spectra.png")

df_eem = generate_eem()
df_eem.to_csv(data_dir / "fluorescence_eem_long.csv", index=False)
plot_eem(df_eem, excitations=range(250,401,5), emissions=range(300,601,5), outpath=plots_dir / "fluorescence_eem.png")
