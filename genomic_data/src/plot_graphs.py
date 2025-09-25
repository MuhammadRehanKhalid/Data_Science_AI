"""
plot_graphs.py
Functions to plot nanodrop, uv-vis and fluorescence eem dataframes.
Uses matplotlib (no seaborn) and saves PNGs.
"""
import matplotlib.pyplot as plt
import numpy as np

def plot_nanodrop(df_long, outpath):
    plt.figure(figsize=(8,4))
    for sid in df_long["sample_id"].unique():
        sub = df_long[df_long["sample_id"]==sid]
        plt.plot(sub["wavelength_nm"], sub["absorbance"], label=sid)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Absorbance (AU)")
    plt.title("Nanodrop Spectra")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

def plot_uvvis(df_long, outpath):
    plt.figure(figsize=(8,4))
    for sid in df_long["sample_id"].unique():
        sub = df_long[df_long["sample_id"]==sid]
        plt.plot(sub["wavelength_nm"], sub["absorbance"], label=sid)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Absorbance (AU)")
    plt.title("UV-Vis Spectra")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

def plot_eem(df_eem_long, excitations, emissions, outpath):
    # Build matrix: rows=excitations, cols=emissions
    ex_vals = np.array(sorted(df_eem_long["excitation_nm"].unique()))
    em_vals = np.array(sorted(df_eem_long["emission_nm"].unique()))
    mat = np.zeros((len(ex_vals), len(em_vals)))
    for _, r in df_eem_long.iterrows():
        ex_i = np.where(ex_vals==r["excitation_nm"])[0][0]
        em_i = np.where(em_vals==r["emission_nm"])[0][0]
        mat[ex_i, em_i] = r["intensity"]
    plt.figure(figsize=(7,5))
    X, Y = np.meshgrid(em_vals, ex_vals)
    plt.pcolormesh(X, Y, mat, shading='auto')
    plt.xlabel("Emission (nm)")
    plt.ylabel("Excitation (nm)")
    plt.title("Fluorescence EEM")
    plt.colorbar(label="Intensity (a.u.)")
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
