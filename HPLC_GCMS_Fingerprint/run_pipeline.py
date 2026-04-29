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

Usage
-----
    python run_pipeline.py                  # default settings
    python run_pipeline.py --reps 20        # more replicates
    python run_pipeline.py --skip-dl        # skip PyTorch training
    python run_pipeline.py --epochs 300     # longer DL training
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
from HPLC_GCMS_Fingerprint.ingestion import MultiTaskDataset
from HPLC_GCMS_Fingerprint.training import train_dl, train_ml
from HPLC_GCMS_Fingerprint.evaluation import (
    evaluate_dl,
    evaluate_ml,
    print_results,
    recommend,
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
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    output_path = Path(args.output)

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
    if not args.skip_dl:
        print("\n" + "="*60)
        print("  Step 6 – Train DL Multi-Task Model (PyTorch)")
        print("="*60)

        dl_model, history = train_dl(
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
        dl_model = None

    # ------------------------------------------------------------------
    # Step 8: Recommendation for a new sample
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 8 – Demonstrate per-sample recommendation")
    print("="*60)

    # Use the first test sample as a "new" sample
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

    print("\n✅  Pipeline completed successfully.\n")


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
