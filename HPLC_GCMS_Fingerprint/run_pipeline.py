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
import json
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Any

from sklearn.model_selection import StratifiedKFold

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
    PHYLA,
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
from HPLC_GCMS_Fingerprint.modules.taxonomy_fetcher import NCBITaxonomyFetcher
from HPLC_GCMS_Fingerprint.modules.sample_data_generator import SampleDataGenerator
from HPLC_GCMS_Fingerprint.modules.biodata_collector import BiodataCollector
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
    plot_phylogenetic_tree,
    plot_prediction_scatter,
    plot_plsda_biplot,
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
        help="Replicates per species (default: 15 -> 90 total samples)",
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
    p.add_argument(
        "--validate-species", action="store_true",
        help=(
            "Validate all species names against NCBI taxonomy before running "
            "the pipeline. Useful for catching misspelled species names."
        ),
    )
    p.add_argument(
        "--skip-optimization", action="store_true",
        help=(
            "Skip hyperparameter optimization and use the exact ML/DL settings "
            "provided via CLI."
        ),
    )
    p.add_argument(
        "--nested-cv", action="store_true",
        help=(
            "Run optional nested cross-validation on the training split for a "
            "more publication-grade estimate of performance."
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
    # Pre-flight Check: Validate Species Names (if requested)
    # ------------------------------------------------------------------
    if args.validate_species:
        print("\n" + "="*60)
        print("  Species Name Validation Check")
        print("="*60)
        
        from HPLC_GCMS_Fingerprint.data_generation.constants import SPECIES
        
        fetcher = NCBITaxonomyFetcher(
            cache_file=output_path.parent / "taxonomy_cache.csv"
        )
        validation_results = fetcher.validate_species_names(SPECIES)
        
        if validation_results['failed']:
            print("\n[ERROR] Species validation failed!")
            print("Please fix the following species names before running the pipeline:")
            for species in validation_results['failed']:
                print(f"  - {species}")
            sys.exit(1)
        else:
            print("\n[OK] All species names validated successfully!")
            print("Proceeding with pipeline...\n")
    
    # ------------------------------------------------------------------
    # Step 0: Data Mode Selection (DUMMY or REAL)
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 0 – Data Mode Selection")
    print("="*60)
    
    data_gen = SampleDataGenerator()
    data_mode = data_gen.ask_data_mode()
    
    # For now, we'll use dummy mode (real mode would require user file input)
    # The interactive choice has been presented
    if data_mode == "real":
        print("\n[NOTE: Real data mode selected, but pipeline currently uses auto-generated dummy data]")
        print("[      To use real data, please modify the pipeline or provide CSV/Excel files]")
        data_mode = "dummy"
    
    print(f"\n[OK] Using {data_mode.upper()} data mode for analysis")
    
    # ------------------------------------------------------------------
    # Step 0.5: Optional Biodata Collection
    # ------------------------------------------------------------------
    biodata_collector = None
    biodata = None
    add_biodata = input("\n" + "="*60 + 
                       "\nWould you like to add sample metadata and growth conditions? (y/n): ").strip().lower()
    
    if add_biodata in ["y", "yes"]:
        print("\n" + "="*60)
        print("  Step 0.5 – Biodata & Growth Conditions Collection")
        print("="*60)
        
        biodata_collector = BiodataCollector(
            output_dir=output_path.parent / "biodata"
        )
        biodata_collector.print_welcome()
        
        # Collect experiment metadata
        collect_exp = input("\nCollect experiment metadata? (y/n, default: y): ").strip().lower()
        if collect_exp != "n":
            biodata_collector.collect_experiment_metadata()
        
        # Collect growth conditions
        collect_growth = input("\nCollect growth conditions? (y/n, default: y): ").strip().lower()
        if collect_growth != "n":
            biodata_collector.collect_growth_conditions()
        
        # Collect medium/nutrients
        collect_medium = input("\nCollect medium and nutrient information? (y/n, default: y): ").strip().lower()
        if collect_medium != "n":
            biodata_collector.collect_medium_and_nutrients()
        
        # Collect environmental conditions
        collect_env = input("\nCollect environmental conditions? (y/n, default: y): ").strip().lower()
        if collect_env != "n":
            biodata_collector.collect_environmental_conditions()
        
        # Save biodata
        save_biodata = input("\nSave biodata to file? (y/n, default: y): ").strip().lower()
        if save_biodata != "n":
            biodata_collector.save_biodata(format="json")
            print(f"[OK] Biodata saved to: {biodata_collector.output_dir}")
        
        biodata = biodata_collector.biodata
        print("\n[OK] Biodata collection complete")
    else:
        print("\n[Skipping biodata collection]")

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
    # Step 4a: Fetch taxonomy for the species present in the dataset
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 4a – Fetch NCBI taxonomy for all species")
    print("="*60)
    taxonomy_df = _fetch_taxonomy_table(
        species_names=sorted(set(hplc_df["species"]).union(set(gcms_df["species"]))),
        cache_path=output_path.parent / "taxonomy_cache.csv",
        output_path=output_path.parent / "species_taxonomy.csv",
    )
    if not taxonomy_df.empty:
        print(f"  Taxonomy records saved: {len(taxonomy_df)}")
        print(f"  Unique species covered : {taxonomy_df['scientific_name'].nunique()}")
    else:
        print("  [No taxonomy records available]")

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
    # Step 4c: Hyperparameter optimization (optional)
    # ------------------------------------------------------------------
    selected_ml_clf = args.ml_clf
    selected_ml_reg = args.ml_reg
    selected_n_estimators_clf = 300
    selected_n_estimators_reg = 200
    selected_dl_params = {
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": 1e-3,
        "dropout": 0.3,
        "patience": 40,
    }

    if not args.skip_optimization:
        print("\n" + "="*60)
        print("  Step 4c – Hyperparameter Optimization")
        print("="*60)

        opt_train_ds, opt_val_ds = train_ds.train_test_split(test_size=0.25, random_state=42)

        print("  [ML] Searching best classifier/regressor combination...")
        ml_opt = _optimize_ml_configs(opt_train_ds, opt_val_ds)
        selected_ml_clf = ml_opt["best"]["clf_type"]
        selected_ml_reg = ml_opt["best"]["reg_type"]
        selected_n_estimators_clf = ml_opt["best"]["n_estimators_clf"]
        selected_n_estimators_reg = ml_opt["best"]["n_estimators_reg"]
        print(
            "  [ML] Best params -> "
            f"clf={selected_ml_clf}, reg={selected_ml_reg}, "
            f"n_estimators_clf={selected_n_estimators_clf}, "
            f"n_estimators_reg={selected_n_estimators_reg}, "
            f"score={ml_opt['best']['score']:.4f}"
        )

        if not args.skip_dl:
            print("  [DL] Searching best training parameters...")
            dl_opt = _optimize_dl_configs(opt_train_ds, opt_val_ds, base_epochs=args.epochs, base_batch_size=args.batch_size)
            if dl_opt is not None:
                selected_dl_params = dl_opt["best"]
                print(
                    "  [DL] Best params -> "
                    f"lr={selected_dl_params['lr']}, "
                    f"dropout={selected_dl_params['dropout']}, "
                    f"batch_size={selected_dl_params['batch_size']}, "
                    f"epochs={selected_dl_params['epochs']}, "
                    f"score={selected_dl_params['score']:.4f}"
                )

    nested_cv_summary: dict[str, Any] = {}
    if args.nested_cv:
        print("\n" + "="*60)
        print("  Step 4d – Nested Cross-Validation")
        print("="*60)
        nested_cv_summary["ml"] = _run_nested_cv_ml(train_ds, random_state=42, outer_splits=3)
        print(
            "  [NESTED CV][ML] mean score = "
            f"{nested_cv_summary['ml']['mean_score']:.4f} ± {nested_cv_summary['ml']['std_score']:.4f}"
        )

        if not args.skip_dl:
            nested_cv_summary["dl"] = _run_nested_cv_dl(
                train_ds,
                random_state=42,
                outer_splits=2,
                base_epochs=selected_dl_params["epochs"],
                base_batch_size=selected_dl_params["batch_size"],
            )
            print(
                "  [NESTED CV][DL] mean score = "
                f"{nested_cv_summary['dl']['mean_score']:.4f} ± {nested_cv_summary['dl']['std_score']:.4f}"
            )

    # ------------------------------------------------------------------
    # Step 5: ML baseline
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 5 – Train ML Multi-Task Baseline (sklearn)")
    print("="*60)
    print(f"  Classifier : {selected_ml_clf}   |  Regressor: {selected_ml_reg}")

    ml_model = train_ml(
        train_ds,
        clf_type=selected_ml_clf,
        reg_type=selected_ml_reg,
        n_estimators_clf=selected_n_estimators_clf,
        n_estimators_reg=selected_n_estimators_reg,
        random_state=42,
    )
    ml_results = evaluate_ml(ml_model, test_ds)
    print_results(ml_results, model_name=f"ML Baseline ({selected_ml_clf} + {selected_ml_reg})")

    # ------------------------------------------------------------------
    # Step 6 & 7: DL model
    # ------------------------------------------------------------------
    dl_model = None
    dl_history: list[dict] = []
    dl_results: dict[str, Any] | None = None

    if not args.skip_dl:
        print("\n" + "="*60)
        print(f"  Step 6 – Train DL Multi-Task Model (PyTorch {args.dl_model.upper()})")
        print("="*60)

        # Keep the test split untouched for final unbiased reporting.
        dl_train_ds, dl_val_ds = train_ds.train_test_split(test_size=0.2, random_state=42)

        dl_model, dl_history = train_dl(
            dl_train_ds,
            dl_val_ds,
            epochs     = selected_dl_params["epochs"],
            batch_size = selected_dl_params["batch_size"],
            lr         = selected_dl_params["lr"],
            dropout    = selected_dl_params["dropout"],
            patience   = selected_dl_params["patience"],
        )
        dl_results = evaluate_dl(dl_model, test_ds)
        print_results(dl_results, model_name=f"DL Multi-Task Model (PyTorch {args.dl_model.upper()})")
    else:
        print("\n  [Skipping DL training as requested]")

    # ------------------------------------------------------------------
    # Step 7b: Best-model selection (ML vs DL)
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 7b – Select Best Model")
    print("="*60)

    model_scores: dict[str, float] = {
        "ML": _aggregate_model_score(ml_results),
    }
    if dl_results is not None:
        model_scores["DL"] = _aggregate_model_score(dl_results)

    for model_name, score in model_scores.items():
        print(f"  {model_name} aggregate score: {score:.4f}")

    best_model_name = max(model_scores, key=model_scores.get)
    print(f"\n  [BEST MODEL] {best_model_name} (highest aggregate score)")

    if best_model_name == "ML":
        print(
            "  Selected config -> "
            f"clf={selected_ml_clf}, reg={selected_ml_reg}, "
            f"n_estimators_clf={selected_n_estimators_clf}, n_estimators_reg={selected_n_estimators_reg}"
        )
    elif dl_results is not None:
        print(
            "  Selected config -> "
            f"lr={selected_dl_params['lr']}, dropout={selected_dl_params['dropout']}, "
            f"batch_size={selected_dl_params['batch_size']}, epochs={selected_dl_params['epochs']}"
        )

    run_artifacts = _save_run_artifacts(
        output_root=output_path.parent,
        args=args,
        dataset=dataset,
        selected_ml={
            "clf": selected_ml_clf,
            "reg": selected_ml_reg,
            "n_estimators_clf": selected_n_estimators_clf,
            "n_estimators_reg": selected_n_estimators_reg,
        },
        selected_dl=selected_dl_params if dl_results is not None else None,
        ml_results=ml_results,
        dl_results=dl_results,
        best_model_name=best_model_name,
        dl_history=dl_history,
        nested_cv_summary=nested_cv_summary,
    )
    print(f"\n  Run metadata exported: {run_artifacts['summary_json']}")

    # ------------------------------------------------------------------
    # Step 8: Recommendation for a new sample
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 8 – Demonstrate per-sample recommendation")
    print("="*60)

    x_new = test_ds.X[0]

    print("\n  -> ML Baseline recommendation:")
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
        print("\n  -> DL Model recommendation:")
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
    print(f"\n  Ground truth -> species: {true_species} | "
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
            taxonomy_df=taxonomy_df,
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
    taxonomy_df,
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

    # 7b. PLS-DA biplot
    plot_plsda_biplot(
        X_raw=dataset.X,
        phylum_labels=dataset.phylum,
        phylum_names=dataset.phylum_names,
        output_path=figures_dir / f"07b_plsda_biplot{ext}",
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

    # 16. Taxonomy-based phylogenetic tree
    plot_phylogenetic_tree(
        taxonomy_df=taxonomy_df,
        output_path=figures_dir / f"16_phylogenetic_tree{ext}",
    )


def _fetch_taxonomy_table(
    *,
    species_names: list[str],
    cache_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    """Fetch and persist taxonomy rows for the species present in this run."""
    fetcher = NCBITaxonomyFetcher(cache_file=cache_path)
    taxonomy_df = fetcher.fetch_batch_taxonomy(species_names)
    if not taxonomy_df.empty:
        taxonomy_df["origin"] = taxonomy_df["species_input"].map(PHYLA).fillna(taxonomy_df.get("phylum", "Unknown"))
        taxonomy_df["species_label"] = taxonomy_df["species_input"]
    taxonomy_df.to_csv(output_path, index=False)
    fetcher.save_cache()
    return taxonomy_df


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


def _aggregate_model_score(results: dict) -> float:
    """
    Convert multi-head metrics into a single comparable score (higher is better).

    The score combines classification quality, recommendation accuracy, and
    regression error terms mapped to a bounded [0, 1] utility.
    """
    cls_terms = [
        float(results["species"]["accuracy"]),
        float(results["species"]["f1_macro"]),
        float(results["phylum"]["accuracy"]),
        float(results["phylum"]["f1_macro"]),
        float(results["best_solvent_accuracy"]),
        float(results["best_assay_accuracy"]),
    ]

    regression_errors = [
        float(results["solvents"]["MAE_overall"]),
        float(results["solvents"]["RMSE_overall"]),
        float(results["assays"]["MAE_overall"]),
        float(results["assays"]["RMSE_overall"]),
    ]
    reg_terms = [1.0 / (1.0 + err) for err in regression_errors]

    all_terms = cls_terms + reg_terms
    return float(np.mean(all_terms))


def _optimize_ml_configs(train_ds: MultiTaskDataset, val_ds: MultiTaskDataset) -> dict:
    """Run a lightweight grid search over ML model families and key params."""
    ml_trials: list[dict[str, Any]] = []

    clf_candidates = ["random_forest", "gradient_boosting", "svm", "logistic_regression"]
    reg_candidates = ["gradient_boosting", "random_forest", "ridge", "lasso"]

    for clf_type in clf_candidates:
        clf_est_grid = [300, 500] if clf_type in {"random_forest", "gradient_boosting"} else [300]
        for reg_type in reg_candidates:
            reg_est_grid = [200, 400] if reg_type in {"random_forest", "gradient_boosting"} else [200]

            for n_estimators_clf in clf_est_grid:
                for n_estimators_reg in reg_est_grid:
                    try:
                        model = train_ml(
                            train_ds,
                            clf_type=clf_type,
                            reg_type=reg_type,
                            n_estimators_clf=n_estimators_clf,
                            n_estimators_reg=n_estimators_reg,
                            random_state=42,
                        )
                        results = evaluate_ml(model, val_ds)
                        score = _aggregate_model_score(results)
                        ml_trials.append(
                            {
                                "clf_type": clf_type,
                                "reg_type": reg_type,
                                "n_estimators_clf": n_estimators_clf,
                                "n_estimators_reg": n_estimators_reg,
                                "score": score,
                            }
                        )
                    except Exception as exc:
                        print(
                            "  [ML OPT] Skipping config "
                            f"clf={clf_type}, reg={reg_type} due to error: {exc}"
                        )

    if not ml_trials:
        return {
            "best": {
                "clf_type": "random_forest",
                "reg_type": "gradient_boosting",
                "n_estimators_clf": 300,
                "n_estimators_reg": 200,
                "score": -1.0,
            },
            "trials": [],
        }

    ml_trials.sort(key=lambda x: x["score"], reverse=True)
    return {"best": ml_trials[0], "trials": ml_trials}


def _optimize_dl_configs(
    train_ds: MultiTaskDataset,
    val_ds: MultiTaskDataset,
    base_epochs: int,
    base_batch_size: int,
) -> dict[str, Any] | None:
    """Run a compact DL hyperparameter search on validation data."""
    dl_trials: list[dict[str, Any]] = []

    search_configs = [
        {"lr": 1e-3, "dropout": 0.3, "batch_size": base_batch_size},
        {"lr": 5e-4, "dropout": 0.3, "batch_size": base_batch_size},
        {"lr": 1e-3, "dropout": 0.2, "batch_size": max(8, base_batch_size)},
    ]
    tune_epochs = min(base_epochs, 120)
    tune_patience = min(20, max(8, tune_epochs // 4))

    for cfg in search_configs:
        try:
            model, _ = train_dl(
                train_ds,
                val_ds,
                epochs=tune_epochs,
                batch_size=cfg["batch_size"],
                lr=cfg["lr"],
                dropout=cfg["dropout"],
                patience=tune_patience,
            )
            results = evaluate_dl(model, val_ds)
            score = _aggregate_model_score(results)

            dl_trials.append(
                {
                    "epochs": base_epochs,
                    "batch_size": cfg["batch_size"],
                    "lr": cfg["lr"],
                    "dropout": cfg["dropout"],
                    "patience": max(20, tune_patience),
                    "score": score,
                }
            )
        except Exception as exc:
            print(
                "  [DL OPT] Skipping config "
                f"lr={cfg['lr']}, dropout={cfg['dropout']} due to error: {exc}"
            )

    if not dl_trials:
        return None

    dl_trials.sort(key=lambda x: x["score"], reverse=True)
    return {"best": dl_trials[0], "trials": dl_trials}


def _run_nested_cv_ml(
    dataset: MultiTaskDataset,
    random_state: int = 42,
    outer_splits: int = 3,
) -> dict[str, Any]:
    """Nested CV for the ML baseline: inner tuning, outer unbiased scoring."""
    outer_cv = StratifiedKFold(n_splits=outer_splits, shuffle=True, random_state=random_state)
    fold_scores: list[float] = []
    fold_params: list[dict[str, Any]] = []

    for fold_idx, (tr_idx, va_idx) in enumerate(outer_cv.split(dataset.X, dataset.species), start=1):
        outer_train = dataset._subset(tr_idx)
        outer_val = dataset._subset(va_idx)
        inner_train, inner_val = outer_train.train_test_split(test_size=0.25, random_state=random_state + fold_idx)

        tuned = _optimize_ml_configs(inner_train, inner_val)
        best = tuned["best"]
        fold_params.append(best)

        model = train_ml(
            outer_train,
            clf_type=best["clf_type"],
            reg_type=best["reg_type"],
            n_estimators_clf=best["n_estimators_clf"],
            n_estimators_reg=best["n_estimators_reg"],
            random_state=random_state,
        )
        results = evaluate_ml(model, outer_val)
        score = _aggregate_model_score(results)
        fold_scores.append(score)
        print(
            f"  [NESTED CV][ML] Fold {fold_idx}/{outer_splits}: "
            f"score={score:.4f} | clf={best['clf_type']} reg={best['reg_type']}"
        )

    return {
        "fold_scores": fold_scores,
        "mean_score": float(np.mean(fold_scores)) if fold_scores else float("nan"),
        "std_score": float(np.std(fold_scores)) if fold_scores else float("nan"),
        "best_params_per_fold": fold_params,
    }


def _run_nested_cv_dl(
    dataset: MultiTaskDataset,
    random_state: int = 42,
    outer_splits: int = 2,
    base_epochs: int = 200,
    base_batch_size: int = 16,
) -> dict[str, Any]:
    """Nested CV for the DL model: compact inner tuning with outer scoring."""
    outer_cv = StratifiedKFold(n_splits=outer_splits, shuffle=True, random_state=random_state)
    fold_scores: list[float] = []
    fold_params: list[dict[str, Any]] = []

    for fold_idx, (tr_idx, va_idx) in enumerate(outer_cv.split(dataset.X, dataset.species), start=1):
        outer_train = dataset._subset(tr_idx)
        outer_val = dataset._subset(va_idx)
        inner_train, inner_val = outer_train.train_test_split(test_size=0.25, random_state=random_state + fold_idx)

        tuned = _optimize_dl_configs(
            inner_train,
            inner_val,
            base_epochs=min(base_epochs, 120),
            base_batch_size=base_batch_size,
        )
        if tuned is None:
            best = {
                "epochs": min(base_epochs, 120),
                "batch_size": base_batch_size,
                "lr": 1e-3,
                "dropout": 0.3,
                "patience": 20,
                "score": float("nan"),
            }
        else:
            best = tuned["best"]
        fold_params.append(best)

        model, _ = train_dl(
            outer_train,
            outer_val,
            epochs=best["epochs"],
            batch_size=best["batch_size"],
            lr=best["lr"],
            dropout=best["dropout"],
            patience=best["patience"],
            random_state=random_state,
        )
        results = evaluate_dl(model, outer_val)
        score = _aggregate_model_score(results)
        fold_scores.append(score)
        print(
            f"  [NESTED CV][DL] Fold {fold_idx}/{outer_splits}: "
            f"score={score:.4f} | lr={best['lr']} dropout={best['dropout']}"
        )

    return {
        "fold_scores": fold_scores,
        "mean_score": float(np.mean(fold_scores)) if fold_scores else float("nan"),
        "std_score": float(np.std(fold_scores)) if fold_scores else float("nan"),
        "best_params_per_fold": fold_params,
    }


def _save_run_artifacts(
    *,
    output_root: Path,
    args: argparse.Namespace,
    dataset,
    selected_ml: dict[str, Any],
    selected_dl: dict[str, Any] | None,
    ml_results: dict[str, Any],
    dl_results: dict[str, Any] | None,
    best_model_name: str,
    dl_history: list[dict[str, Any]],
    nested_cv_summary: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Persist run parameters and outcomes for reproducibility and publications."""
    results_dir = output_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = results_dir / f"run_summary_{ts}.json"
    ml_metrics_path = results_dir / f"metrics_ml_{ts}.csv"
    dl_metrics_path = results_dir / f"metrics_dl_{ts}.csv"
    dl_history_path = results_dir / f"dl_history_{ts}.csv"

    score_board = {
        "ML": _aggregate_model_score(ml_results),
    }
    if dl_results is not None:
        score_board["DL"] = _aggregate_model_score(dl_results)

    summary_payload = {
        "timestamp": ts,
        "cli_args": vars(args),
        "data_summary": {
            "n_samples": int(len(dataset)),
            "n_features": int(dataset.X.shape[1]),
            "n_species": int(len(dataset.species_names)),
            "n_phyla": int(len(dataset.phylum_names)),
            "n_solvents": int(len(dataset.solvent_names)),
            "n_assays": int(len(dataset.assay_names)),
        },
        "selected_ml": selected_ml,
        "selected_dl": selected_dl,
        "score_board": score_board,
        "best_model": best_model_name,
        "nested_cv": nested_cv_summary or {},
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    pd.DataFrame(_flatten_metrics_for_csv(ml_results, model_name="ML")).to_csv(
        ml_metrics_path, index=False
    )

    if dl_results is not None:
        pd.DataFrame(_flatten_metrics_for_csv(dl_results, model_name="DL")).to_csv(
            dl_metrics_path, index=False
        )

    if dl_history:
        pd.DataFrame(dl_history).to_csv(dl_history_path, index=False)

    return {
        "summary_json": str(summary_path),
        "ml_metrics_csv": str(ml_metrics_path),
        "dl_metrics_csv": str(dl_metrics_path) if dl_results is not None else "",
        "dl_history_csv": str(dl_history_path) if dl_history else "",
    }


def _flatten_metrics_for_csv(results: dict[str, Any], model_name: str) -> list[dict[str, Any]]:
    """Convert nested metrics dict into flat rows for easier article tables."""
    rows = [
        {"model": model_name, "metric": "species_accuracy", "value": float(results["species"]["accuracy"] )},
        {"model": model_name, "metric": "species_f1_macro", "value": float(results["species"]["f1_macro"] )},
        {"model": model_name, "metric": "phylum_accuracy", "value": float(results["phylum"]["accuracy"] )},
        {"model": model_name, "metric": "phylum_f1_macro", "value": float(results["phylum"]["f1_macro"] )},
        {"model": model_name, "metric": "solvents_mae", "value": float(results["solvents"]["MAE_overall"] )},
        {"model": model_name, "metric": "solvents_rmse", "value": float(results["solvents"]["RMSE_overall"] )},
        {"model": model_name, "metric": "assays_mae", "value": float(results["assays"]["MAE_overall"] )},
        {"model": model_name, "metric": "assays_rmse", "value": float(results["assays"]["RMSE_overall"] )},
        {"model": model_name, "metric": "best_solvent_accuracy", "value": float(results["best_solvent_accuracy"] )},
        {"model": model_name, "metric": "best_assay_accuracy", "value": float(results["best_assay_accuracy"] )},
        {"model": model_name, "metric": "aggregate_score", "value": _aggregate_model_score(results)},
    ]
    return rows


if __name__ == "__main__":
    main()

