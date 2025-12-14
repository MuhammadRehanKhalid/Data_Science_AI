import argparse
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.formula.api import ols
import statsmodels.api as sm
from pathlib import Path
from sklearn.manifold import TSNE
import umap.umap_ as umap


def eda(df: pd.DataFrame, outdir: Path, plots: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    plots.mkdir(parents=True, exist_ok=True)

    # Summary tables
    grp = df.groupby(["Algal_Class", "Solvent"]).agg({
        "Extraction_Yield_mg_per_g": ["mean", "std"],
        "FRAP": ["mean", "std"],
        "ABTS": ["mean", "std"],
        "DPPH": ["mean", "std"],
        "ORAC": ["mean", "std"],
        "TPC": ["mean", "std"],
    }).reset_index()
    grp.columns = ["_".join([c for c in col if c]) for col in grp.columns.values]
    grp.to_csv(outdir / "group_summary.csv", index=False)

    # Correlation heatmap
    corr_cols = ["Extraction_Yield_mg_per_g", "FRAP", "ABTS", "DPPH", "ORAC", "TPC"]
    corr = df[corr_cols].corr()
    plt.figure(figsize=(6, 5))
    sns.heatmap(corr, annot=True, cmap="viridis", vmin=0, vmax=1)
    plt.title("Assay/Yield Correlations")
    plt.tight_layout()
    plt.savefig(plots / "corr_heatmap.png", dpi=200)
    plt.close()

    # Boxplots per solvent
    for col in ["FRAP", "ABTS", "DPPH", "ORAC", "TPC", "Extraction_Yield_mg_per_g"]:
        plt.figure(figsize=(10, 5))
        sns.boxplot(data=df, x="Solvent", y=col)
        plt.xticks(rotation=25, ha="right")
        plt.title(f"{col} by Solvent")
        plt.tight_layout()
        plt.savefig(plots / f"box_{col}_by_solvent.png", dpi=200)
        plt.close()

    # PCA-like viz (standardized features)
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    X = df[corr_cols].values
    Xs = StandardScaler().fit_transform(X)
    pca = PCA(n_components=2)
    comps = pca.fit_transform(Xs)
    pca_df = pd.DataFrame(comps, columns=["PC1", "PC2"])
    pca_df["Solvent"] = df["Solvent"].values
    plt.figure(figsize=(7,5))
    sns.scatterplot(data=pca_df, x="PC1", y="PC2", hue="Solvent")
    plt.title("PCA of assays+yield (colored by solvent)")
    plt.tight_layout()
    plt.savefig(plots / "pca_scatter.png", dpi=200)
    plt.close()

    # UMAP of assay+yields
    reducer = umap.UMAP(n_components=2, random_state=42)
    um = reducer.fit_transform(Xs)
    um_df = pd.DataFrame(um, columns=["UMAP1","UMAP2"])
    um_df["Solvent"] = df["Solvent"].values
    plt.figure(figsize=(7,5))
    sns.scatterplot(data=um_df, x="UMAP1", y="UMAP2", hue="Solvent")
    plt.title("UMAP of assays+yield (colored by solvent)")
    plt.tight_layout()
    plt.savefig(plots / "umap_scatter.png", dpi=200)
    plt.close()

    # t-SNE as alternative
    tsne = TSNE(n_components=2, random_state=42, perplexity=30)
    ts = tsne.fit_transform(Xs)
    ts_df = pd.DataFrame(ts, columns=["TSNE1","TSNE2"])
    ts_df["Solvent"] = df["Solvent"].values
    plt.figure(figsize=(7,5))
    sns.scatterplot(data=ts_df, x="TSNE1", y="TSNE2", hue="Solvent")
    plt.title("t-SNE of assays+yield (colored by solvent)")
    plt.tight_layout()
    plt.savefig(plots / "tsne_scatter.png", dpi=200)
    plt.close()

    # Two-way ANOVA example: FRAP ~ C(Solvent) + C(Algal_Class)
    model = ols('FRAP ~ C(Solvent) + C(Algal_Class)', data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    anova_table.to_csv(outdir / "anova_FRAP.csv")

    # Markdown summary
    with open(outdir / "eda_summary.md", "w", encoding="utf-8") as f:
        f.write("# EDA Summary\n\n")
        f.write("## Group Means (per Algal Class x Solvent)\n\n")
        f.write(grp.head(20).to_markdown(index=False))
        f.write("\n\n## Correlation Matrix\n\n")
        f.write(corr.to_markdown())
        f.write("\n\n## ANOVA (FRAP)\n\n")
        f.write(anova_table.to_markdown())
    print(f"EDA complete. Outputs in {outdir} and plots in {plots}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--outdir", default="reports")
    ap.add_argument("--plots", default="plots")
    args = ap.parse_args()
    df = pd.read_csv(args.data)
    eda(df, Path(args.outdir), Path(args.plots))


if __name__ == "__main__":
    main()
