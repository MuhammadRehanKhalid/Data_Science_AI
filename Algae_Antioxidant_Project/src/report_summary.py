import argparse
from pathlib import Path
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projroot", default="Algae_Antioxidant_Project")
    args = ap.parse_args()
    root = Path(args.projroot)
    reports = root / "reports"
    plots = root / "plots"

    eda_md = (reports / "eda_summary.md").read_text(encoding="utf-8") if (reports / "eda_summary.md").exists() else "(EDA summary not found)"
    ml_df = pd.read_csv(reports / "ml_results.csv") if (reports / "ml_results.csv").exists() else pd.DataFrame()
    dl_df = pd.read_csv(reports / "dl_results.csv") if (reports / "dl_results.csv").exists() else pd.DataFrame()

    # Best models per target
    best_rows = []
    if not ml_df.empty:
        for tgt in ml_df["target"].unique():
            sub = ml_df[ml_df["target"] == tgt].sort_values(by=["R2"], ascending=False)
            if len(sub):
                best_rows.append(sub.iloc[0])
    best_df = pd.DataFrame(best_rows)

    out_md = []
    out_md.append("# Project Summary\n")
    out_md.append("\n## EDA Highlights\n\n")
    out_md.append(eda_md)
    out_md.append("\n\n## Best ML Models (by R2)\n\n")
    out_md.append(best_df.to_markdown(index=False) if not best_df.empty else "(No ML results)")
    out_md.append("\n\n## DL Results\n\n")
    out_md.append(dl_df.to_markdown(index=False) if not dl_df.empty else "(No DL results)")
    out_md.append("\n\n## Key Plots\n\n")
    key_plots = [
        "corr_heatmap.png","pca_scatter.png","umap_scatter.png","tsne_scatter.png",
        "parity_XGBoost_FRAP.png","parity_XGBoost_ABTS.png","parity_XGBoost_DPPH.png","parity_XGBoost_ORAC.png","parity_XGBoost_TPC.png",
        "shap_summary_FRAP.png","shap_bar_FRAP.png"
    ]
    for kp in key_plots:
        if (plots / kp).exists():
            out_md.append(f"- {kp}")
    summary_path = reports / "project_summary.md"
    summary_path.write_text("\n".join(out_md), encoding="utf-8")
    print(f"Wrote summary: {summary_path}")

if __name__ == "__main__":
    main()
