"""
run_pipeline.py – End-to-end demonstration of the HPLC / GC-MS multi-task
                   modeling pipeline.

Steps
-----
  1. Generate dummy HPLC + GC-MS fingerprint data (reproducible).
  2. Export to a multi-sheet Excel workbook.
  3. Load and validate the workbook.
  4. Build the feature matrix and multi-task target arrays.
  4b. (Optional) Print data-driven model recommendation.
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
    python run_pipeline.py --figure-format jpg    # export figures as JPEG
    python run_pipeline.py --figure-format pdf    # export figures as PDF
    python run_pipeline.py --figure-format docx   # export figures as Word docs
    python run_pipeline.py --recommend-model      # print model selection guidance
    python run_pipeline.py --ml-clf svm           # use SVM classifier
    python run_pipeline.py --ml-reg ridge         # use Ridge regressor
    python run_pipeline.py --dl-model cnn         # use CNN encoder
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path when running as a script
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import numpy as np

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
from HPLC_GCMS_Fingerprint.models import recommend_model
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
    p.add_argument(
        "--figure-format", type=str, default="png",
        choices=["png", "jpg", "pdf", "docx"],
        help=(
            "Export format for all generated figures. "
            "Choices: png (default), jpg, pdf, docx (Word document)."
        ),
    )
    # ------------------------------------------------------------------
    # Model selection
    # ------------------------------------------------------------------
    p.add_argument(
        "--ml-clf", type=str, default="random_forest",
        choices=["random_forest", "gradient_boosting", "svm", "knn", "logistic_regression"],
        help=(
            "Classifier type for the ML species/phylum heads. "
            "Default: random_forest."
        ),
    )
    p.add_argument(
        "--ml-reg", type=str, default="gradient_boosting",
        choices=["gradient_boosting", "random_forest", "ridge", "lasso", "svm", "knn"],
        help=(
            "Regressor type for the ML solvent/assay heads. "
            "Default: gradient_boosting."
        ),
    )
    p.add_argument(
        "--dl-model", type=str, default="mlp",
        choices=["mlp", "cnn"],
        help=(
            "Deep-learning encoder architecture. "
            "'mlp' = multi-layer perceptron (default); "
            "'cnn' = 1-D convolutional encoder for spectral data."
        ),
    )
    p.add_argument(
        "--recommend-model", action="store_true",
        help=(
            "Analyse your dataset and print a data-driven recommendation "
            "on which ML/DL model to use, with a clear explanation."
        ),
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
    # Step 4b: Model recommendation (optional)
    # ------------------------------------------------------------------
    if args.recommend_model:
        rec = recommend_model(
            n_samples=len(dataset),
            n_features=dataset.X.shape[1],
            skip_dl=args.skip_dl,
        )
        print(rec["reasoning"])

    # ------------------------------------------------------------------
    # Step 5: ML baseline
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 5 – Train ML Multi-Task Baseline (sklearn)")
    print("="*60)
    print(f"  Classifier : {args.ml_clf}   |  Regressor: {args.ml_reg}")

    ml_model = train_ml(
        train_ds,
        clf_type=args.ml_clf,
        reg_type=args.ml_reg,
        random_state=42,
    )
    ml_results = evaluate_ml(ml_model, test_ds)
    print_results(ml_results, model_name=f"ML Baseline ({args.ml_clf} + {args.ml_reg})")

    # ------------------------------------------------------------------
    # Step 6 & 7: DL model
    # ------------------------------------------------------------------
    dl_model = None
    dl_history: list[dict] = []

    if not args.skip_dl:
        print("\n" + "="*60)
        print(f"  Step 6 – Train DL Multi-Task Model (PyTorch {args.dl_model.upper()})")
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
        print_results(dl_results, model_name=f"DL Multi-Task Model (PyTorch {args.dl_model.upper()})")
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
            figure_format=args.figure_format,
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
    figure_format: str = "png",
) -> None:
    import torch
    figures_dir.mkdir(parents=True, exist_ok=True)
    ext = f".{figure_format}"

    # 1. HPLC chromatograms
    plot_hplc_chromatogram(
        hplc_df, HPLC_RT_CENTERS,
        output_path=figures_dir / f"01_hplc_chromatograms{ext}",
    )

    # 2. GC-MS spectra
    plot_gcms_spectrum(
        gcms_df, MZ_BIN_CENTERS,
        output_path=figures_dir / f"02_gcms_spectra{ext}",
    )

    # 3. Assay score heatmap
    plot_assay_heatmap(
        hplc_df, ASSAYS, SOLVENTS,
        output_path=figures_dir / f"03_assay_heatmap{ext}",
    )

    # 4. Solvent heatmap
    plot_solvent_heatmap(
        hplc_df, SOLVENTS,
        output_path=figures_dir / f"04_solvent_heatmap{ext}",
    )

    # 5. Assay box plots by phylum
    plot_assay_boxplots(
        hplc_df, ASSAYS, SOLVENTS,
        output_path=figures_dir / f"05_assay_boxplots{ext}",
    )

    # 6. Solvent grouped bars by phylum
    plot_solvent_barplots(
        hplc_df, SOLVENTS,
        output_path=figures_dir / f"06_solvent_barplots{ext}",
    )

    # 7. PCA biplot
    plot_pca_biplot(
        X_raw=dataset.X,
        phylum_labels=dataset.phylum,
        phylum_names=dataset.phylum_names,
        output_path=figures_dir / f"07_pca_biplot{ext}",
    )

    # 8. Confusion matrices – ML model
    ml_preds = ml_model.predict(test_ds.X)
    plot_confusion_matrix(
        test_ds.species, ml_preds["pred_species"],
        class_names=dataset.species_names,
        title="Species Classification – ML Baseline",
        output_path=figures_dir / f"08a_confusion_species_ml{ext}",
    )
    plot_confusion_matrix(
        test_ds.phylum, ml_preds["pred_phylum"],
        class_names=dataset.phylum_names,
        title="Phylum Classification – ML Baseline",
        output_path=figures_dir / f"08b_confusion_phylum_ml{ext}",
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
            output_path=figures_dir / f"08c_confusion_species_dl{ext}",
        )
        plot_confusion_matrix(
            test_ds.phylum, dl_out["pred_phylum"].cpu().numpy(),
            class_names=dataset.phylum_names,
            title="Phylum Classification – DL Model",
            output_path=figures_dir / f"08d_confusion_phylum_dl{ext}",
        )

    # 9. DL training curves
    if dl_history:
        plot_training_curves(
            dl_history,
            output_path=figures_dir / f"09_training_curves{ext}",
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
        output_path=figures_dir / f"10_feature_importance{ext}",
    )

    # 11. Predicted vs true scatter – solvent head
    plot_prediction_scatter(
        test_ds.y_solvents,
        ml_preds["pred_solvents"],
        output_names=dataset.solvent_names,
        title="Solvent Activity – ML Predicted vs True",
        output_path=figures_dir / f"11a_scatter_solvents_ml{ext}",
    )
    plot_prediction_scatter(
        test_ds.y_assays,
        ml_preds["pred_assays"],
        output_names=dataset.assay_names,
        title="Assay Performance – ML Predicted vs True",
        output_path=figures_dir / f"11b_scatter_assays_ml{ext}",
    )

    if dl_model is not None:
        with torch.no_grad():
            dl_sol_pred = dl_out["pred_solvents"].cpu().numpy()
            dl_ass_pred = dl_out["pred_assays"].cpu().numpy()
        plot_prediction_scatter(
            test_ds.y_solvents, dl_sol_pred,
            output_names=dataset.solvent_names,
            title="Solvent Activity – DL Predicted vs True",
            output_path=figures_dir / f"11c_scatter_solvents_dl{ext}",
        )
        plot_prediction_scatter(
            test_ds.y_assays, dl_ass_pred,
            output_names=dataset.assay_names,
            title="Assay Performance – DL Predicted vs True",
            output_path=figures_dir / f"11d_scatter_assays_dl{ext}",
        )

    # 12. Radar chart – solvent performance per species
    plot_radar_solvent(
        hplc_df, SOLVENTS,
        output_path=figures_dir / f"12_radar_solvent{ext}",
    )

    # 13. Phylum × assay recommendation
    plot_phylum_assay_recommendation(
        hplc_df, ASSAYS, SOLVENTS,
        output_path=figures_dir / f"13_phylum_assay_recommendation{ext}",
    )

    # 14. Solvent × assay interaction
    plot_solvent_assay_interaction(
        hplc_df, ASSAYS, SOLVENTS,
        output_path=figures_dir / f"14_solvent_assay_interaction{ext}",
    )

    # 15. Best-solvent distribution per phylum
    plot_best_solvent_distribution(
        hplc_df, SOLVENTS,
        output_path=figures_dir / f"15_best_solvent_distribution{ext}",
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

