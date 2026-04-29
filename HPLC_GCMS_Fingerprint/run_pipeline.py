"""
run_pipeline.py – End-to-end demonstration of the HPLC / GC-MS multi-task
                   modeling pipeline.

Steps
-----
  1. Generate dummy HPLC + GC-MS fingerprint data (reproducible).
  2. Export to a multi-sheet Excel workbook.
  3. Load and validate the workbook.
  4. Build the feature matrix and multi-task target arrays.
  5. Train the ML baseline (sklearn).
  6. Train the DL multi-task model (PyTorch).
  7. Evaluate both models.
  8. Demonstrate per-sample solvent / assay recommendation.
  9. Generate all visualisation figures (R-Studio-style).

Usage
-----
    python run_pipeline.py                        # default settings
    python run_pipeline.py --reps 20              # more replicates
    python run_pipeline.py --skip-dl              # skip PyTorch training
    python run_pipeline.py --epochs 300           # longer DL training
    python run_pipeline.py --figures-dir figures  # custom figure output dir
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path when running as a script
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
from HPLC_GCMS_Fingerprint.data_generation import (
    export_to_excel,
    generate_gcms,
    generate_hplc,
)
from HPLC_GCMS_Fingerprint.data_generation.constants import (
    ASSAYS,
    HPLC_RT_CENTERS,
    MZ_BIN_CENTERS,
    SOLVENTS,
)
from HPLC_GCMS_Fingerprint.ingestion import MultiTaskDataset
from HPLC_GCMS_Fingerprint.training import train_dl, train_ml
from HPLC_GCMS_Fingerprint.evaluation import (
    evaluate_dl,
    evaluate_ml,
    print_results,
    recommend,
)
from HPLC_GCMS_Fingerprint.visualization import (
    plot_assay_boxplots,
    plot_assay_heatmap,
    plot_best_solvent_distribution,
    plot_confusion_matrix,
    plot_feature_importance,
    plot_gcms_spectrum,
    plot_hplc_chromatogram,
    plot_phylum_assay_recommendation,
    plot_pca_biplot,
    plot_prediction_scatter,
    plot_radar_solvent,
    plot_solvent_assay_interaction,
    plot_solvent_barplots,
    plot_solvent_heatmap,
    plot_training_curves,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="HPLC/GC-MS Multi-Task Pipeline")
    p.add_argument(
        "--reps", type=int, default=15,
        help="Replicates per species (default: 15 → 90 total samples)",
    )
    p.add_argument(
        "--output", type=str, default="HPLC_GCMS_Fingerprint/data/fingerprint_data.xlsx",
        help="Path for the generated Excel workbook.",
    )
    p.add_argument(
        "--representation", type=str, default="combined",
        choices=["raw", "binned", "binary", "meta", "combined"],
        help="Feature representation to use.",
    )
    p.add_argument(
        "--epochs", type=int, default=200,
        help="DL training epochs.",
    )
    p.add_argument(
        "--batch-size", type=int, default=16,
        help="DL mini-batch size.",
    )
    p.add_argument(
        "--skip-dl", action="store_true",
        help="Skip the PyTorch DL model (ML baseline only).",
    )
    p.add_argument(
        "--figures-dir", type=str, default="HPLC_GCMS_Fingerprint/figures",
        help="Output directory for all generated figures.",
    )
    p.add_argument(
        "--skip-figures", action="store_true",
        help="Skip figure generation.",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    figures_dir = Path(args.figures_dir)

    # ------------------------------------------------------------------
    # Step 1 & 2: Generate dummy data and export to Excel
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 1 – Generate dummy HPLC & GC-MS fingerprint data")
    print("="*60)

    hplc_df = generate_hplc(n_replicates=args.reps, random_seed=42)
    gcms_df = generate_gcms(n_replicates=args.reps, random_seed=43)

    print(f"  HPLC samples : {len(hplc_df)}")
    print(f"  GC-MS samples: {len(gcms_df)}")
    print(f"  HPLC columns : {len(hplc_df.columns)}")
    print(f"  GC-MS columns: {len(gcms_df.columns)}")
    print(f"  Assays       : {ASSAYS}")

    print("\n" + "="*60)
    print("  Step 2 – Export to Excel")
    print("="*60)
    export_to_excel(hplc_df, gcms_df, output_path=output_path)

    # ------------------------------------------------------------------
    # Step 3 & 4: Ingest and build feature matrix
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 3 – Load, validate, engineer features")
    print("="*60)

    dataset = MultiTaskDataset.from_excel(
        output_path,
        representation=args.representation,
    )
    print(f"  {dataset}")

    train_ds, test_ds = dataset.train_test_split(test_size=0.2, random_state=42)
    print(f"  Train: {len(train_ds)} samples  |  Test: {len(test_ds)} samples")

    # ------------------------------------------------------------------
    # Step 5: ML baseline
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 5 – Train ML Multi-Task Baseline (sklearn)")
    print("="*60)

    ml_model = train_ml(train_ds, random_state=42)
    ml_results = evaluate_ml(ml_model, test_ds)
    print_results(ml_results, model_name="ML Baseline (RandomForest + GBR)")

    # ------------------------------------------------------------------
    # Step 6 & 7: DL model
    # ------------------------------------------------------------------
    dl_model = None
    dl_history: list[dict] = []

    if not args.skip_dl:
        print("\n" + "="*60)
        print("  Step 6 – Train DL Multi-Task Model (PyTorch)")
        print("="*60)

        dl_model, dl_history = train_dl(
            train_ds,
            test_ds,
            epochs     = args.epochs,
            batch_size = args.batch_size,
            lr         = 1e-3,
            dropout    = 0.3,
            patience   = 40,
        )
        dl_results = evaluate_dl(dl_model, test_ds)
        print_results(dl_results, model_name="DL Multi-Task Model (PyTorch MLP)")
    else:
        print("\n  [Skipping DL training as requested]")

    # ------------------------------------------------------------------
    # Step 8: Recommendation for a new sample
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 8 – Demonstrate per-sample recommendation")
    print("="*60)

    x_new = test_ds.X[0]

    print("\n  → ML Baseline recommendation:")
    rec_ml = recommend(
        ml_model, x_new,
        solvent_names=dataset.solvent_names,
        assay_names  =dataset.assay_names,
        species_names=dataset.species_names,
        phylum_names =dataset.phylum_names,
        is_dl=False,
    )
    _print_recommendation(rec_ml)

    if dl_model is not None:
        print("\n  → DL Model recommendation:")
        rec_dl = recommend(
            dl_model, x_new,
            solvent_names=dataset.solvent_names,
            assay_names  =dataset.assay_names,
            species_names=dataset.species_names,
            phylum_names =dataset.phylum_names,
            is_dl=True,
        )
        _print_recommendation(rec_dl)

    true_species  = dataset.species_names[test_ds.species[0]]
    true_solvent  = test_ds.best_solvent[0]
    true_assay    = test_ds.best_assay[0]
    print(f"\n  Ground truth → species: {true_species} | "
          f"best_solvent: {true_solvent} | best_assay: {true_assay}")

    # ------------------------------------------------------------------
    # Step 9: Visualisations
    # ------------------------------------------------------------------
    if not args.skip_figures:
        print("\n" + "="*60)
        print("  Step 9 – Generating Figures")
        print("="*60)
        _generate_figures(
            hplc_df=hplc_df,
            gcms_df=gcms_df,
            dataset=dataset,
            train_ds=train_ds,
            test_ds=test_ds,
            ml_model=ml_model,
            ml_results=ml_results,
            dl_model=dl_model,
            dl_history=dl_history,
            figures_dir=figures_dir,
        )
        print(f"\n  All figures saved to: {figures_dir}/")

    print("\n✅  Pipeline completed successfully.\n")


# ---------------------------------------------------------------------------
# Figure generation
# ---------------------------------------------------------------------------

def _generate_figures(
    *,
    hplc_df,
    gcms_df,
    dataset,
    train_ds,
    test_ds,
    ml_model,
    ml_results,
    dl_model,
    dl_history,
    figures_dir: Path,
) -> None:
    import torch
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. HPLC chromatograms
    plot_hplc_chromatogram(
        hplc_df, HPLC_RT_CENTERS,
        output_path=figures_dir / "01_hplc_chromatograms.png",
    )

    # 2. GC-MS spectra
    plot_gcms_spectrum(
        gcms_df, MZ_BIN_CENTERS,
        output_path=figures_dir / "02_gcms_spectra.png",
    )

    # 3. Assay score heatmap
    plot_assay_heatmap(
        hplc_df, ASSAYS, SOLVENTS,
        output_path=figures_dir / "03_assay_heatmap.png",
    )

    # 4. Solvent heatmap
    plot_solvent_heatmap(
        hplc_df, SOLVENTS,
        output_path=figures_dir / "04_solvent_heatmap.png",
    )

    # 5. Assay box plots by phylum
    plot_assay_boxplots(
        hplc_df, ASSAYS, SOLVENTS,
        output_path=figures_dir / "05_assay_boxplots.png",
    )

    # 6. Solvent grouped bars by phylum
    plot_solvent_barplots(
        hplc_df, SOLVENTS,
        output_path=figures_dir / "06_solvent_barplots.png",
    )

    # 7. PCA biplot
    plot_pca_biplot(
        X_raw=dataset.X,
        phylum_labels=dataset.phylum,
        phylum_names=dataset.phylum_names,
        output_path=figures_dir / "07_pca_biplot.png",
    )

    # 8. Confusion matrices – ML model
    ml_preds = ml_model.predict(test_ds.X)
    plot_confusion_matrix(
        test_ds.species, ml_preds["pred_species"],
        class_names=dataset.species_names,
        title="Species Classification – ML Baseline",
        output_path=figures_dir / "08a_confusion_species_ml.png",
    )
    plot_confusion_matrix(
        test_ds.phylum, ml_preds["pred_phylum"],
        class_names=dataset.phylum_names,
        title="Phylum Classification – ML Baseline",
        output_path=figures_dir / "08b_confusion_phylum_ml.png",
    )

    # 8c. Confusion matrices – DL model
    if dl_model is not None:
        dev = torch.device("cpu")
        X_t = torch.tensor(test_ds.X, dtype=torch.float32).to(dev)
        with torch.no_grad():
            dl_out = dl_model.predict(X_t)
        plot_confusion_matrix(
            test_ds.species, dl_out["pred_species"].cpu().numpy(),
            class_names=dataset.species_names,
            title="Species Classification – DL Model",
            output_path=figures_dir / "08c_confusion_species_dl.png",
        )
        plot_confusion_matrix(
            test_ds.phylum, dl_out["pred_phylum"].cpu().numpy(),
            class_names=dataset.phylum_names,
            title="Phylum Classification – DL Model",
            output_path=figures_dir / "08d_confusion_phylum_dl.png",
        )

    # 9. DL training curves
    if dl_history:
        plot_training_curves(
            dl_history,
            output_path=figures_dir / "09_training_curves.png",
        )

    # 10. Feature importance (RF species head)
    import numpy as np
    rf = ml_model.head_species.named_steps["clf"]
    importances = rf.feature_importances_
    # Build feature names: combined = raw(130) + binned(20) + binary(130) + meta(12) = 292
    _feat_names = (
        [f"RT_{i+1:02d}_raw" for i in range(50)] +
        [f"mz_{j+1:03d}_raw" for j in range(80)] +
        [f"RT_bin{k+1}" for k in range(10)] +
        [f"mz_bin{k+1}" for k in range(10)] +
        [f"RT_{i+1:02d}_bin" for i in range(50)] +
        [f"mz_{j+1:03d}_bin" for j in range(80)] +
        [f"HPLC_meta_{m}" for m in ["mean","std","npks","skew","max","div"]] +
        [f"GCMS_meta_{m}" for m in ["mean","std","npks","skew","max","div"]]
    )
    if len(_feat_names) != len(importances):
        _feat_names = [f"feat_{i}" for i in range(len(importances))]
    plot_feature_importance(
        importances, _feat_names,
        title="RF Feature Importance – Species Head",
        output_path=figures_dir / "10_feature_importance.png",
    )

    # 11. Predicted vs true scatter – solvent head
    plot_prediction_scatter(
        test_ds.y_solvents,
        ml_preds["pred_solvents"],
        output_names=dataset.solvent_names,
        title="Solvent Activity – ML Predicted vs True",
        output_path=figures_dir / "11a_scatter_solvents_ml.png",
    )
    plot_prediction_scatter(
        test_ds.y_assays,
        ml_preds["pred_assays"],
        output_names=dataset.assay_names,
        title="Assay Performance – ML Predicted vs True",
        output_path=figures_dir / "11b_scatter_assays_ml.png",
    )

    if dl_model is not None:
        with torch.no_grad():
            dl_sol_pred = dl_out["pred_solvents"].cpu().numpy()
            dl_ass_pred = dl_out["pred_assays"].cpu().numpy()
        plot_prediction_scatter(
            test_ds.y_solvents, dl_sol_pred,
            output_names=dataset.solvent_names,
            title="Solvent Activity – DL Predicted vs True",
            output_path=figures_dir / "11c_scatter_solvents_dl.png",
        )
        plot_prediction_scatter(
            test_ds.y_assays, dl_ass_pred,
            output_names=dataset.assay_names,
            title="Assay Performance – DL Predicted vs True",
            output_path=figures_dir / "11d_scatter_assays_dl.png",
        )

    # 12. Radar chart – solvent performance per species
    plot_radar_solvent(
        hplc_df, SOLVENTS,
        output_path=figures_dir / "12_radar_solvent.png",
    )

    # 13. Phylum × assay recommendation
    plot_phylum_assay_recommendation(
        hplc_df, ASSAYS, SOLVENTS,
        output_path=figures_dir / "13_phylum_assay_recommendation.png",
    )

    # 14. Solvent × assay interaction
    plot_solvent_assay_interaction(
        hplc_df, ASSAYS, SOLVENTS,
        output_path=figures_dir / "14_solvent_assay_interaction.png",
    )

    # 15. Best-solvent distribution per phylum
    plot_best_solvent_distribution(
        hplc_df, SOLVENTS,
        output_path=figures_dir / "15_best_solvent_distribution.png",
    )


def _print_recommendation(rec: dict) -> None:
    print(f"     Predicted species  : {rec['predicted_species']}")
    print(f"     Predicted phylum   : {rec['predicted_phylum']}")
    print(f"     Best solvent       : {rec['best_solvent']}")
    sol_str = ", ".join(
        f"{k}={v:.3f}" for k, v in rec["solvent_activities"].items()
    )
    print(f"     Solvent activities : {sol_str}")
    print(f"     Best assay         : {rec['best_assay']}")
    ass_str = ", ".join(
        f"{k}={v:.3f}" for k, v in rec["assay_performances"].items()
    )
    print(f"     Assay performances : {ass_str}")


if __name__ == "__main__":
    main()

