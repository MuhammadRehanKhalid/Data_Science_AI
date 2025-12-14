# Algae Antioxidant Project

This workspace compares solvent systems for extracting antioxidant compounds from diverse algae and builds ML/DL models to predict antioxidant capacity.

## Structure
- data/: synthetic and real datasets
- src/: scripts for data generation, EDA, modeling
- plots/: saved figures
- reports/: CSV/Markdown summaries

## Quick Start (Windows PowerShell)
```
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src\generate_dummy_data.py --out data\algae_antioxidants_dummy.csv
python src\analysis_basic.py --data data\algae_antioxidants_dummy.csv --outdir reports --plots plots
python src\modeling_ml.py --data data\algae_antioxidants_dummy.csv --outdir reports --plots plots
python src\modeling_dl.py --data data\algae_antioxidants_dummy.csv --outdir reports --plots plots
```

## Expected Outputs
- reports/eda_summary.md: overview tables (group means, ANOVA), correlations.
- reports/ml_results.csv: CV metrics (R2, RMSE, MAE) per model.
- reports/dl_results.csv: test metrics and training curves.
- plots/: heatmaps, PCA, boxplots, feature importance, parity plots.

## Notes
- Dummy data simulates solvent polarity effects, assay correlations (FRAP/ABTS/DPPH/ORAC/TPC), and algae-class differences.
- Replace dummy data with your measured dataset to run the same pipeline.
