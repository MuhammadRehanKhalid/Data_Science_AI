"""
Visualization module for the HPLC / GC-MS multi-task pipeline.

All figures use a publication-quality R-Studio-inspired style:
  • White / near-white background, light grid lines
  • ggplot2-compatible colour palettes (Set1 / custom)
  • Clean typography, clearly labelled axes and titles
  • Saved as high-resolution PNG (300 dpi)

Public functions
----------------
plot_hplc_chromatogram          – RT vs intensity, one trace per species
plot_gcms_spectrum              – m/z bar spectrum, one panel per species
plot_assay_heatmap              – mean assay score ×  species/phylum
plot_solvent_heatmap            – mean activity × species/phylum per solvent
plot_assay_boxplots             – per-phylum box-whisker for each assay
plot_solvent_barplots           – grouped bars: mean activity per solvent × phylum
plot_pca_biplot                 – PCA of fingerprint features coloured by phylum
plot_confusion_matrix           – classification results heatmap
plot_training_curves            – DL training/val loss over epochs
plot_feature_importance         – top-N RF feature importances
plot_prediction_scatter         – true vs predicted regression values
plot_radar_solvent              – radar chart of solvent scores per species
plot_phylum_assay_recommendation– which assay to recommend per phylum (heatmap)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import matplotlib
matplotlib.use("Agg")   # non-interactive backend – safe in pipelines

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Global style – mimics ggplot2 / R Studio look
# ---------------------------------------------------------------------------

_PALETTE_PHYLA = {
    "Chlorophyta":   "#4DAF4A",
    "Cyanobacteria": "#377EB8",
    "Rhodophyta":    "#E41A1C",
    "Phaeophyceae":  "#FF7F00",
}

_PALETTE_ASSAYS = {
    "DPPH": "#E41A1C",
    "ABTS": "#377EB8",
    "FRAP": "#4DAF4A",
    "HPPT": "#FF7F00",
    "TPC":  "#984EA3",
}

_PALETTE_SOLVENTS = {
    "Water":        "#1F78B4",
    "MeOH_70":      "#33A02C",
    "EtOH_70":      "#E31A1C",
    "EtOAc":        "#FF7F00",
    "Acetone_100":  "#6A3D9A",
    "MeCN_50":      "#B15928",
}

_RSTUDIO_RCPARAMS = {
    "figure.facecolor":   "white",
    "axes.facecolor":     "#F8F8F8",
    "axes.edgecolor":     "#CCCCCC",
    "axes.linewidth":     0.8,
    "axes.grid":          True,
    "grid.color":         "#E0E0E0",
    "grid.linestyle":     "-",
    "grid.linewidth":     0.5,
    "font.family":        "DejaVu Sans",
    "font.size":          10,
    "axes.titlesize":     12,
    "axes.labelsize":     10,
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "legend.fontsize":    9,
    "legend.frameon":     True,
    "legend.framealpha":  0.9,
    "legend.edgecolor":   "#CCCCCC",
    "figure.dpi":         150,
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
}

_RSTUDIO_CMAP = LinearSegmentedColormap.from_list(
    "rstudio_div",
    ["#2166AC", "#F7F7F7", "#D6604D"],
)


def _apply_style() -> None:
    plt.rcParams.update(_RSTUDIO_RCPARAMS)


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [Figure] Saved → {path}")


# ---------------------------------------------------------------------------
# 1. HPLC Chromatogram overlay
# ---------------------------------------------------------------------------

def plot_hplc_chromatogram(
    hplc_df: pd.DataFrame,
    rt_centers: np.ndarray,
    output_path: Path,
    n_samples_per_species: int = 3,
) -> None:
    """
    Overlay HPLC chromatograms (RT vs intensity) for representative samples,
    one colour per species/phylum.
    """
    _apply_style()
    species_list = sorted(hplc_df["species"].unique())
    intensity_cols = sorted([c for c in hplc_df.columns if c.startswith("intensity_RT_")])

    fig, axes = plt.subplots(
        len(species_list), 1,
        figsize=(12, 2.5 * len(species_list)),
        sharex=True,
    )
    if len(species_list) == 1:
        axes = [axes]

    phylum_of = dict(zip(hplc_df["species"], hplc_df["phylum"]))
    phylum_colors = {}
    for i, ph in enumerate(sorted(set(hplc_df["phylum"]))):
        phylum_colors[ph] = list(_PALETTE_PHYLA.values())[i % len(_PALETTE_PHYLA)]

    for ax, sp in zip(axes, species_list):
        sub = hplc_df[hplc_df["species"] == sp].head(n_samples_per_species)
        ph = phylum_of[sp]
        color = phylum_colors.get(ph, "#333333")

        for rep_idx, (_, row) in enumerate(sub.iterrows()):
            intensities = row[intensity_cols].to_numpy(dtype=float)
            alpha = 0.9 - rep_idx * 0.2
            ax.plot(
                rt_centers, intensities,
                color=color, alpha=alpha, linewidth=0.9,
                label=f"Rep {int(row['replicate'])}" if rep_idx == 0 else "_nolegend_",
            )
            ax.fill_between(rt_centers, intensities, alpha=0.08, color=color)

        ax.set_ylabel("Intensity (AU)", fontsize=9)
        ax.set_title(f"{sp}  [{ph}]", fontsize=10, loc="left", pad=4)
        ax.set_xlim(rt_centers[0], rt_centers[-1])

    axes[-1].set_xlabel("Retention Time (min)", fontsize=10)
    fig.suptitle("HPLC Chromatogram Profiles by Species", fontsize=13, y=1.01, fontweight="bold")
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 2. GC-MS spectrum (m/z bar chart)
# ---------------------------------------------------------------------------

def plot_gcms_spectrum(
    gcms_df: pd.DataFrame,
    mz_centers: np.ndarray,
    output_path: Path,
    n_cols: int = 3,
) -> None:
    """
    Plot mean GC-MS m/z spectrum for each species as a bar chart panel.
    """
    _apply_style()
    species_list = sorted(gcms_df["species"].unique())
    n_sp = len(species_list)
    mz_cols = sorted([c for c in gcms_df.columns if c.startswith("intensity_mz_")])

    n_rows = (n_sp + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 5, n_rows * 3.2), sharey=False)
    axes_flat = np.array(axes).flatten() if n_sp > 1 else [axes]

    phylum_of = {row["species"]: row["phylum"] for _, row in gcms_df[["species","phylum"]].drop_duplicates().iterrows()}
    phylum_colors = {}
    for i, ph in enumerate(sorted(set(gcms_df["phylum"]))):
        phylum_colors[ph] = list(_PALETTE_PHYLA.values())[i % len(_PALETTE_PHYLA)]

    for ax, sp in zip(axes_flat, species_list):
        sub = gcms_df[gcms_df["species"] == sp]
        mean_int = sub[mz_cols].mean().to_numpy(dtype=float)
        ph = phylum_of[sp]
        color = phylum_colors.get(ph, "#555555")

        ax.bar(mz_centers, mean_int, width=(mz_centers[1]-mz_centers[0])*0.8,
               color=color, alpha=0.8, edgecolor="none")
        ax.set_title(sp, fontsize=9, pad=3)
        ax.set_xlabel("m/z (Da)", fontsize=8)
        ax.set_ylabel("Mean Intensity", fontsize=8)

    for ax in axes_flat[n_sp:]:
        ax.set_visible(False)

    fig.suptitle("GC-MS Mean Spectrum by Species", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 3. Assay score heatmap (species/phylum × assay)
# ---------------------------------------------------------------------------

def plot_assay_heatmap(
    hplc_df: pd.DataFrame,
    assays: list[str],
    solvents: list[str],
    output_path: Path,
) -> None:
    """
    Heatmap of mean assay score per species, averaged across solvents.
    Also produces a phylum-level summary.
    """
    _apply_style()
    records = []
    for sp in sorted(hplc_df["species"].unique()):
        ph = hplc_df.loc[hplc_df["species"] == sp, "phylum"].iloc[0]
        for assay in assays:
            vals = []
            for sol in solvents:
                col = f"{assay}_{sol}"
                if col in hplc_df.columns:
                    vals.extend(hplc_df.loc[hplc_df["species"] == sp, col].tolist())
            records.append({
                "species": sp,
                "phylum":  ph,
                "assay":   assay,
                "mean_score": float(np.mean(vals)) if vals else 0.0,
            })

    df_records = pd.DataFrame(records)

    # --- Species-level heatmap ---
    pivot_sp = df_records.pivot(index="species", columns="assay", values="mean_score")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.heatmap(
        pivot_sp, ax=axes[0],
        cmap="YlOrRd", annot=True, fmt=".1f",
        linewidths=0.4, linecolor="#CCCCCC",
        cbar_kws={"label": "Mean Score (0–100)"},
    )
    axes[0].set_title("Assay Scores by Species\n(mean across solvents)", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Assay", fontsize=10)
    axes[0].set_ylabel("")
    axes[0].tick_params(axis="x", rotation=0)
    axes[0].tick_params(axis="y", rotation=0)

    # --- Phylum-level heatmap ---
    pivot_ph = df_records.groupby(["phylum", "assay"])["mean_score"].mean().reset_index()
    pivot_ph = pivot_ph.pivot(index="phylum", columns="assay", values="mean_score")

    sns.heatmap(
        pivot_ph, ax=axes[1],
        cmap="Blues", annot=True, fmt=".1f",
        linewidths=0.4, linecolor="#CCCCCC",
        cbar_kws={"label": "Mean Score (0–100)"},
    )
    axes[1].set_title("Assay Scores by Phylum\n(mean across species & solvents)", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Assay", fontsize=10)
    axes[1].set_ylabel("")
    axes[1].tick_params(axis="x", rotation=0)
    axes[1].tick_params(axis="y", rotation=0)

    fig.suptitle("Antioxidant Assay Performance", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 4. Solvent × species/phylum heatmap
# ---------------------------------------------------------------------------

def plot_solvent_heatmap(
    hplc_df: pd.DataFrame,
    solvents: list[str],
    output_path: Path,
) -> None:
    """
    Heatmap: mean combined antioxidant activity per (species × solvent)
    and per (phylum × solvent).
    """
    _apply_style()
    records = []
    for sp in sorted(hplc_df["species"].unique()):
        ph = hplc_df.loc[hplc_df["species"] == sp, "phylum"].iloc[0]
        for sol in solvents:
            col = f"activity_{sol}"
            if col in hplc_df.columns:
                mean_val = float(hplc_df.loc[hplc_df["species"] == sp, col].mean())
            else:
                mean_val = 0.0
            records.append({"species": sp, "phylum": ph, "solvent": sol, "activity": mean_val})

    df_r = pd.DataFrame(records)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    pivot_sp = df_r.pivot(index="species", columns="solvent", values="activity")
    sns.heatmap(
        pivot_sp, ax=axes[0],
        cmap="RdYlGn", annot=True, fmt=".1f",
        linewidths=0.4, linecolor="#CCCCCC",
        cbar_kws={"label": "Mean Activity (0–100)"},
    )
    axes[0].set_title("Extraction Efficiency by Species × Solvent", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Solvent", fontsize=10)
    axes[0].set_ylabel("")
    axes[0].tick_params(axis="x", rotation=30, ha="right")
    axes[0].tick_params(axis="y", rotation=0)

    pivot_ph = df_r.groupby(["phylum","solvent"])["activity"].mean().reset_index()
    pivot_ph = pivot_ph.pivot(index="phylum", columns="solvent", values="activity")
    sns.heatmap(
        pivot_ph, ax=axes[1],
        cmap="RdYlGn", annot=True, fmt=".1f",
        linewidths=0.4, linecolor="#CCCCCC",
        cbar_kws={"label": "Mean Activity (0–100)"},
    )
    axes[1].set_title("Extraction Efficiency by Phylum × Solvent", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Solvent", fontsize=10)
    axes[1].set_ylabel("")
    axes[1].tick_params(axis="x", rotation=30, ha="right")
    axes[1].tick_params(axis="y", rotation=0)

    fig.suptitle("Solvent Extraction Efficiency", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 5. Box plots: assay scores by phylum
# ---------------------------------------------------------------------------

def plot_assay_boxplots(
    hplc_df: pd.DataFrame,
    assays: list[str],
    solvents: list[str],
    output_path: Path,
) -> None:
    """
    For each assay, draw a box-whisker plot of scores split by phylum,
    pooled across solvents.
    """
    _apply_style()
    rows = []
    for _, row in hplc_df.iterrows():
        for assay in assays:
            for sol in solvents:
                col = f"{assay}_{sol}"
                if col in hplc_df.columns:
                    rows.append({
                        "phylum": row["phylum"],
                        "species": row["species"],
                        "assay":  assay,
                        "score":  float(row[col]),
                    })

    df_long = pd.DataFrame(rows)
    phyla = sorted(df_long["phylum"].unique())
    palette = {ph: _PALETTE_PHYLA.get(ph, "#888888") for ph in phyla}

    n_assays = len(assays)
    n_cols = min(3, n_assays)
    n_rows = (n_assays + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 4.5, n_rows * 4), sharey=False)
    axes_flat = np.array(axes).flatten() if n_assays > 1 else [axes]

    for ax, assay in zip(axes_flat, assays):
        sub = df_long[df_long["assay"] == assay]
        order = sorted(sub["phylum"].unique())
        sns.boxplot(
            data=sub, x="phylum", y="score", order=order,
            palette=palette, ax=ax,
            width=0.6, flierprops=dict(marker="o", markersize=3, alpha=0.5),
            linewidth=0.8,
        )
        sns.stripplot(
            data=sub, x="phylum", y="score", order=order,
            palette=palette, ax=ax, size=3, alpha=0.35, jitter=True,
        )
        ax.set_title(f"{assay} by Phylum", fontsize=10, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel("Score (0–100)", fontsize=9)
        ax.tick_params(axis="x", rotation=30, labelsize=8)
        ax.set_xticklabels(ax.get_xticklabels(), ha="right")

    for ax in axes_flat[n_assays:]:
        ax.set_visible(False)

    fig.suptitle("Antioxidant Assay Scores by Phylum\n(pooled across solvents)", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 6. Grouped bar plots: solvent performance by phylum
# ---------------------------------------------------------------------------

def plot_solvent_barplots(
    hplc_df: pd.DataFrame,
    solvents: list[str],
    output_path: Path,
) -> None:
    """
    Grouped bar chart: mean combined activity per solvent, grouped by phylum.
    """
    _apply_style()
    rows = []
    for _, row in hplc_df.iterrows():
        for sol in solvents:
            col = f"activity_{sol}"
            if col in hplc_df.columns:
                rows.append({"phylum": row["phylum"], "solvent": sol, "activity": float(row[col])})

    df_long = pd.DataFrame(rows)
    phyla = sorted(df_long["phylum"].unique())
    sol_palette = [_PALETTE_SOLVENTS.get(s, "#888888") for s in solvents]

    fig, axes = plt.subplots(1, len(phyla), figsize=(3.5 * len(phyla), 5), sharey=True)
    if len(phyla) == 1:
        axes = [axes]

    for ax, ph in zip(axes, phyla):
        sub = df_long[df_long["phylum"] == ph]
        means = sub.groupby("solvent")["activity"].mean().reindex(solvents)
        sems  = sub.groupby("solvent")["activity"].sem().reindex(solvents).fillna(0)

        bars = ax.bar(
            solvents, means.values, color=sol_palette, alpha=0.85,
            edgecolor="white", linewidth=0.5,
            yerr=sems.values, capsize=3, error_kw={"linewidth": 0.8, "ecolor": "#555"},
        )
        ax.set_title(ph, fontsize=10, fontweight="bold")
        ax.set_xlabel("Solvent", fontsize=9)
        ax.set_ylabel("Mean Activity (0–100)", fontsize=9) if ax == axes[0] else None
        ax.tick_params(axis="x", rotation=40, labelsize=8)
        ax.set_xticklabels(solvents, ha="right", fontsize=8)

    fig.suptitle("Solvent Extraction Activity by Phylum", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 7. PCA biplot coloured by phylum
# ---------------------------------------------------------------------------

def plot_pca_biplot(
    X_raw: np.ndarray,
    phylum_labels: np.ndarray,
    phylum_names: list[str],
    output_path: Path,
) -> None:
    """
    PCA of the (standardised) fingerprint feature matrix, coloured by phylum.
    """
    _apply_style()
    pca = PCA(n_components=2, random_state=42)
    X_scaled = StandardScaler().fit_transform(X_raw)
    coords = pca.fit_transform(X_scaled)

    fig, ax = plt.subplots(figsize=(7, 6))

    palette_list = list(_PALETTE_PHYLA.values())
    for i, ph in enumerate(phylum_names):
        mask = phylum_labels == i
        color = _PALETTE_PHYLA.get(ph, palette_list[i % len(palette_list)])
        ax.scatter(
            coords[mask, 0], coords[mask, 1],
            label=ph, color=color, alpha=0.75, s=40, edgecolors="white", linewidths=0.4,
        )

    var1 = pca.explained_variance_ratio_[0] * 100
    var2 = pca.explained_variance_ratio_[1] * 100
    ax.set_xlabel(f"PC1 ({var1:.1f}% variance)", fontsize=10)
    ax.set_ylabel(f"PC2 ({var2:.1f}% variance)", fontsize=10)
    ax.set_title("PCA of Fingerprint Features — Coloured by Phylum", fontsize=12, fontweight="bold")
    ax.legend(title="Phylum", fontsize=9, title_fontsize=9)
    ax.axhline(0, color="#AAAAAA", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="#AAAAAA", linewidth=0.5, linestyle="--")

    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 8. Confusion matrix
# ---------------------------------------------------------------------------

def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str],
    title: str,
    output_path: Path,
) -> None:
    """
    Annotated confusion matrix heatmap, with row-normalised percentages.
    """
    from sklearn.metrics import confusion_matrix as _cm

    _apply_style()
    cm = _cm(y_true, y_pred, labels=list(range(len(class_names))))
    cm_norm = cm.astype(float) / (cm.sum(axis=1, keepdims=True) + 1e-9) * 100

    fig, ax = plt.subplots(figsize=(max(5, len(class_names)), max(4, len(class_names))))
    sns.heatmap(
        cm_norm, ax=ax,
        cmap="Blues", annot=True, fmt=".1f",
        xticklabels=class_names, yticklabels=class_names,
        linewidths=0.4, linecolor="#DDDDDD",
        vmin=0, vmax=100,
        cbar_kws={"label": "Row %"},
    )
    ax.set_xlabel("Predicted", fontsize=10)
    ax.set_ylabel("True", fontsize=10)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.tick_params(axis="x", rotation=40)
    ax.tick_params(axis="y", rotation=0)

    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 9. Training curves (DL)
# ---------------------------------------------------------------------------

def plot_training_curves(
    history: list[dict],
    output_path: Path,
) -> None:
    """
    Plot training and validation loss components over epochs.
    """
    _apply_style()
    epochs = [h["epoch"] for h in history]
    train_total = [h["train"]["total"] for h in history]
    val_total = [h["val_loss"] for h in history]

    components = ["species", "phylum", "solvents", "assays"]
    comp_colors = {"species": "#E41A1C", "phylum": "#377EB8", "solvents": "#4DAF4A", "assays": "#FF7F00"}

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    # Panel 1: total loss
    ax = axes[0]
    ax.plot(epochs, train_total, color="#333333", linewidth=1.5, label="Train total")
    ax.plot(epochs, val_total, color="#E41A1C", linewidth=1.5, linestyle="--", label="Val total")
    ax.set_xlabel("Epoch", fontsize=10)
    ax.set_ylabel("Loss", fontsize=10)
    ax.set_title("Total Training Loss", fontsize=11, fontweight="bold")
    ax.legend()

    # Panel 2: component losses (training)
    ax = axes[1]
    for comp in components:
        vals = [h["train"][comp] for h in history if comp in h.get("train", {})]
        if vals:
            ax.plot(epochs[:len(vals)], vals, color=comp_colors[comp], linewidth=1.2, label=comp)
    ax.set_xlabel("Epoch", fontsize=10)
    ax.set_ylabel("Component Loss", fontsize=10)
    ax.set_title("Training Loss Components", fontsize=11, fontweight="bold")
    ax.legend()

    fig.suptitle("DL Multi-Task Model – Training Curves", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 10. Feature importance (ML)
# ---------------------------------------------------------------------------

def plot_feature_importance(
    importances: np.ndarray,
    feature_names: list[str],
    title: str,
    output_path: Path,
    top_n: int = 25,
) -> None:
    """
    Horizontal bar chart of top-N feature importances from a tree model.
    """
    _apply_style()
    idx = np.argsort(importances)[-top_n:]
    fi = importances[idx]
    fn = [feature_names[i] for i in idx]

    fig, ax = plt.subplots(figsize=(8, max(4, top_n * 0.3)))
    colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(fi)))
    ax.barh(fn, fi, color=colors, edgecolor="none")
    ax.set_xlabel("Importance", fontsize=10)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 11. Predicted vs true scatter (regression)
# ---------------------------------------------------------------------------

def plot_prediction_scatter(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_names: list[str],
    title: str,
    output_path: Path,
) -> None:
    """
    Scatter plot of true vs predicted values for each regression output.
    """
    _apply_style()
    n_out = y_true.shape[1]
    n_cols = min(3, n_out)
    n_rows = (n_out + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 3.8, n_rows * 3.8))
    axes_flat = np.array(axes).flatten() if n_out > 1 else [axes]

    palette_list = ["#1F78B4", "#33A02C", "#E31A1C", "#FF7F00", "#6A3D9A", "#B15928"]

    for i, (ax, name) in enumerate(zip(axes_flat, output_names)):
        yt = y_true[:, i]
        yp = y_pred[:, i]
        color = palette_list[i % len(palette_list)]

        ax.scatter(yt, yp, alpha=0.55, s=22, color=color, edgecolors="none")
        lo, hi = min(yt.min(), yp.min()), max(yt.max(), yp.max())
        ax.plot([lo, hi], [lo, hi], "k--", linewidth=0.8, alpha=0.6)

        from sklearn.metrics import r2_score, mean_absolute_error
        r2  = r2_score(yt, yp) if yt.std() > 0 else float("nan")
        mae = mean_absolute_error(yt, yp)
        ax.set_title(name, fontsize=10, fontweight="bold")
        ax.set_xlabel("True", fontsize=9)
        ax.set_ylabel("Predicted", fontsize=9)
        ax.text(
            0.05, 0.92, f"R²={r2:.2f}  MAE={mae:.3f}",
            transform=ax.transAxes, fontsize=8, color="#333",
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7),
        )

    for ax in axes_flat[n_out:]:
        ax.set_visible(False)

    fig.suptitle(title, fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 12. Radar chart: solvent performance per species
# ---------------------------------------------------------------------------

def plot_radar_solvent(
    hplc_df: pd.DataFrame,
    solvents: list[str],
    output_path: Path,
) -> None:
    """
    Radar / spider chart: mean combined antioxidant activity per solvent,
    one trace per species.
    """
    _apply_style()
    species_list = sorted(hplc_df["species"].unique())
    n_sol = len(solvents)
    angles = np.linspace(0, 2 * np.pi, n_sol, endpoint=False).tolist()
    angles += angles[:1]   # close polygon

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.set_facecolor("#F8F8F8")

    palette_sp = plt.cm.tab10(np.linspace(0, 0.9, len(species_list)))

    for sp, color in zip(species_list, palette_sp):
        sub = hplc_df[hplc_df["species"] == sp]
        means = [float(sub[f"activity_{s}"].mean()) if f"activity_{s}" in sub else 0 for s in solvents]
        means += means[:1]
        ax.plot(angles, means, linewidth=1.5, linestyle="solid", color=color, label=sp)
        ax.fill(angles, means, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(solvents, fontsize=9)
    ax.set_yticks([20, 40, 60, 80])
    ax.set_yticklabels(["20", "40", "60", "80"], fontsize=7, color="#666")
    ax.set_rlabel_position(30)
    ax.set_title("Solvent Performance per Species (Radar Chart)", fontsize=12, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)

    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 13. Phylum × Assay recommendation heatmap
# ---------------------------------------------------------------------------

def plot_phylum_assay_recommendation(
    hplc_df: pd.DataFrame,
    assays: list[str],
    solvents: list[str],
    output_path: Path,
) -> None:
    """
    For each phylum, show the mean assay score (best solvent only) as a heatmap,
    and annotate which assay is recommended.
    """
    _apply_style()
    records = []
    for _, row in hplc_df.iterrows():
        ph = row["phylum"]
        # Identify best solvent for this row
        sol_scores = {sol: row.get(f"activity_{sol}", 0.0) for sol in solvents}
        best_sol = max(sol_scores, key=sol_scores.get)
        for assay in assays:
            col = f"{assay}_{best_sol}"
            val = float(row[col]) if col in hplc_df.columns else 0.0
            records.append({"phylum": ph, "assay": assay, "score": val})

    df_r = pd.DataFrame(records)
    pivot = df_r.groupby(["phylum","assay"])["score"].mean().reset_index()
    pivot = pivot.pivot(index="phylum", columns="assay", values="score")

    # Row-normalise so each phylum sums to 100 (shows relative recommendation)
    pivot_norm = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Raw scores
    sns.heatmap(
        pivot, ax=axes[0],
        cmap="YlOrRd", annot=True, fmt=".1f",
        linewidths=0.4, linecolor="#CCCCCC",
        cbar_kws={"label": "Mean Score (best solvent)"},
    )
    axes[0].set_title("Mean Assay Score per Phylum\n(using best solvent per sample)", fontsize=11, fontweight="bold")
    axes[0].tick_params(axis="x", rotation=0)
    axes[0].tick_params(axis="y", rotation=0)
    axes[0].set_xlabel("Assay")
    axes[0].set_ylabel("")

    # Normalised (recommendation strength)
    sns.heatmap(
        pivot_norm, ax=axes[1],
        cmap="Purples", annot=True, fmt=".1f",
        linewidths=0.4, linecolor="#CCCCCC",
        cbar_kws={"label": "Relative Recommendation (%)"},
    )
    axes[1].set_title("Recommended Assay per Phylum\n(normalised relative strength)", fontsize=11, fontweight="bold")
    axes[1].tick_params(axis="x", rotation=0)
    axes[1].tick_params(axis="y", rotation=0)
    axes[1].set_xlabel("Assay")
    axes[1].set_ylabel("")

    fig.suptitle("Phylum-Level Assay Recommendation", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 14. Solvent × Assay interaction heatmap (all solvents, all assays)
# ---------------------------------------------------------------------------

def plot_solvent_assay_interaction(
    hplc_df: pd.DataFrame,
    assays: list[str],
    solvents: list[str],
    output_path: Path,
) -> None:
    """
    Heatmap: mean assay score per (solvent × assay) averaged over all species.
    Reveals which solvent–assay combinations are most productive.
    """
    _apply_style()
    matrix = pd.DataFrame(index=solvents, columns=assays, dtype=float)
    for sol in solvents:
        for assay in assays:
            col = f"{assay}_{sol}"
            if col in hplc_df.columns:
                matrix.loc[sol, assay] = float(hplc_df[col].mean())

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(
        matrix.astype(float), ax=ax,
        cmap="viridis", annot=True, fmt=".1f",
        linewidths=0.4, linecolor="#CCCCCC",
        cbar_kws={"label": "Mean Score (0–100)"},
    )
    ax.set_title("Solvent × Assay Interaction\n(mean score across all species)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Assay", fontsize=10)
    ax.set_ylabel("Solvent", fontsize=10)
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)

    fig.tight_layout()
    _save(fig, output_path)


# ---------------------------------------------------------------------------
# 15. Best-solvent distribution per phylum (stacked bar)
# ---------------------------------------------------------------------------

def plot_best_solvent_distribution(
    hplc_df: pd.DataFrame,
    solvents: list[str],
    output_path: Path,
) -> None:
    """
    Stacked bar chart showing how often each solvent is 'best' per phylum.
    """
    _apply_style()
    records = []
    for _, row in hplc_df.iterrows():
        sol_scores = {sol: row.get(f"activity_{sol}", 0.0) for sol in solvents}
        best_sol = max(sol_scores, key=sol_scores.get)
        records.append({"phylum": row["phylum"], "best_solvent": best_sol})

    df_r = pd.DataFrame(records)
    counts = df_r.groupby(["phylum","best_solvent"]).size().unstack(fill_value=0)
    counts_pct = counts.div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(9, 5))
    sol_colors = [_PALETTE_SOLVENTS.get(s, "#888") for s in counts_pct.columns]
    counts_pct.plot(
        kind="bar", stacked=True, ax=ax, color=sol_colors,
        edgecolor="white", linewidth=0.4,
    )
    ax.set_ylabel("Frequency (%)", fontsize=10)
    ax.set_xlabel("Phylum", fontsize=10)
    ax.set_title("Distribution of Best Solvent per Phylum", fontsize=12, fontweight="bold")
    ax.legend(title="Solvent", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=9)
    ax.tick_params(axis="x", rotation=30)

    fig.tight_layout()
    _save(fig, output_path)
