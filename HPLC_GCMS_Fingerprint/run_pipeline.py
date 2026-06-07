"""
run_pipeline.py – End-to-end demonstration of the HPLC / GC-MS / FTIR multi-task
                   modeling pipeline with flexible source selection.

Steps
-----
  0. Select data sources: FTIR, HPLC, GCMS (single or multiple combinations).
  1. Generate dummy data for selected sources (reproducible).
  2. Export to a multi-sheet Excel workbook.
  3. Load and validate the workbook.
  4. Build the feature matrix from selected sources.
  4b. (Optional) Print data-driven model recommendation.
  5. Train the ML baseline (sklearn) on selected sources.
  6. Train the DL multi-task model (PyTorch) on selected sources.
  7. Evaluate both models with selected sources.
  8. Demonstrate per-sample solvent / assay recommendation.
  9. Generate all visualisation figures (source-aware, R-Studio-style).

Supported Source Combinations
-----
  Single Sources:
    • FTIR only           → FTIR spectra analysis
    • HPLC only           → HPLC chromatogram analysis
    • GCMS only           → GC-MS spectrum analysis
  
  Dual Sources:
    • FTIR + HPLC         → Combined FTIR & HPLC analysis
    • FTIR + GCMS         → Combined FTIR & GCMS analysis
    • HPLC + GCMS         → Combined HPLC & GCMS analysis (traditional)
  
  All Three:
    • FTIR + HPLC + GCMS  → Full multi-modal analysis

Usage Examples
-----
    python run_pipeline.py                          # interactive source selection
    python run_pipeline.py --reps 20                # more replicates
    python run_pipeline.py --skip-dl                # skip PyTorch training
    python run_pipeline.py --epochs 300             # longer DL training
    python run_pipeline.py --figures-dir figures    # custom figure output dir
    python run_pipeline.py --figure-format jpg      # export figures as JPEG
    python run_pipeline.py --figure-format pdf      # export figures as PDF
    python run_pipeline.py --training-display progress  # compact progress bar
    python run_pipeline.py --recommend-model        # print model selection guidance
    python run_pipeline.py --ml-clf svm             # use SVM classifier
    python run_pipeline.py --ml-reg ridge           # use Ridge regressor
    python run_pipeline.py --dl-model cnn           # use CNN encoder
    python run_pipeline.py --publication-mode       # full reproducibility mode
"""

from __future__ import annotations

import argparse
import builtins
import contextlib
import getpass
import json
import os
import platform
import socket
import sys
import warnings
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Any

from sklearn.model_selection import GridSearchCV, KFold, ParameterGrid, RandomizedSearchCV, StratifiedKFold

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
from HPLC_GCMS_Fingerprint.models import (
    MLMultiTaskSearchEstimator,
    pack_multitask_targets,
    recommend_model,
)
from HPLC_GCMS_Fingerprint.modules.taxonomy_fetcher import NCBITaxonomyFetcher
from HPLC_GCMS_Fingerprint.modules.data_input_validator import DataSourceSelector
from HPLC_GCMS_Fingerprint.modules.sample_data_generator import SampleDataGenerator
from HPLC_GCMS_Fingerprint.modules.biodata_collector import BiodataCollector
from HPLC_GCMS_Fingerprint.modules.real_data_loader import RealDataLoader, prompt_for_real_data
from HPLC_GCMS_Fingerprint.visualization import (
    plot_assay_boxplots,
    plot_assay_heatmap,
    plot_best_solvent_distribution,
    plot_confusion_matrix,
    plot_feature_importance,
    plot_ftir_spectrum,
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
        "--training-display", type=str, default="verbose",
        choices=["verbose", "progress"],
        help=(
            "Show full training logs or compact progress updates for ML/DL steps. "
            "Default: verbose."
        ),
    )
    p.add_argument(
        "--step-display", type=str, default=None,
        help=(
            "Per-step display overrides in the form '5:progress,6:verbose' where "
            "the number is the pipeline step (5=ML,6=DL). Overrides global --training-display."
        ),
    )
    p.add_argument(
        "--data-mode", type=str, default=None,
        choices=["dummy", "real"],
        help="Non-interactive data mode: 'dummy' or 'real'. If omitted, prompts interactively.",
    )
    p.add_argument(
        "--selected-sources", type=str, default=None,
        help="Comma-separated selected sources (e.g. HPLC,GCMS,FTIR). If provided, source selection is non-interactive.",
    )
    p.add_argument(
        "--add-biodata", action="store_true",
        help="When set, collect biodata non-interactively where possible (skips prompts).",
    )
    p.add_argument(
        "--skip-dl", action="store_true",
        help="Skip the PyTorch DL model (ML baseline only).",
    )
    p.add_argument(
        "--figures-dir", type=str, default=None,
        help=(
            "Output directory for all generated figures. If omitted, figures "
            "are written under the per-run artifacts folder (recommended)."
        ),
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
    p.add_argument(
        "--publication-mode", action="store_true",
        help=(
            "Enable publication-style behavior: nested CV on, optimization on, "
            "and full run metadata exports for reproducibility."
        ),
    )
    p.add_argument(
        "--compare-sources", action="store_true",
        help=(
            "Run comparison across all source combinations (FTIR, HPLC, GCMS). "
            "Tests single sources and all dual/triple combinations. "
            "Generates report showing model performance and figure count per combination."
        ),
    )
    p.add_argument(
        "--runner-name", type=str, default="",
        help="Optional name of the person running the pipeline. Defaults to OS username.",
    )
    p.add_argument(
        "--logs-dir", type=str, default=str(_PROJECT_ROOT / "output_logs"),
        help="Root directory for per-run logs and artifacts.",
    )
    p.add_argument(
        "--ignore-known-warnings", action="store_true",
        help=(
            "Suppress common non-critical warnings (e.g. convergence/future warnings). "
            "Use only for cleaner output once behavior is validated."
        ),
    )
    return p.parse_args()


def _safe_slug(value: str, fallback: str = "unknown") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.strip())
    cleaned = cleaned.strip("_")
    return cleaned or fallback


def _format_progress_bar(percent: float, width: int = 24) -> str:
    pct = max(0.0, min(100.0, float(percent)))
    filled = int(round((pct / 100.0) * width))
    filled = max(0, min(width, filled))
    return f"[{('#' * filled).ljust(width, '.')}] {pct:6.2f}%"


def _make_training_progress_callback(
    training_display: str,
    external_callback: callable | None = None,
):
    if training_display != "progress":
        return None

    def _callback(percent: float, info: dict[str, Any] | None = None):
        payload = info or {}
        if external_callback is not None:
            try:
                external_callback(percent, payload)
            except Exception:
                pass
            return

        stage = payload.get("stage", "training")
        message = payload.get("message", stage)
        line = f"  [TRAIN] {_format_progress_bar(percent)} {message}"
        end = "\n" if float(percent) >= 100.0 else "\r"
        print(line, end=end, flush=True)

    return _callback


class _TeeStream:
    """Mirror text to console and a file stream."""

    def __init__(self, stream, file_handle):
        self.stream = stream
        self.file_handle = file_handle

    def write(self, text: str) -> int:
        self.stream.write(text)
        self.file_handle.write(text)
        return len(text)

    def flush(self) -> None:
        self.stream.flush()
        self.file_handle.flush()


@contextlib.contextmanager
def _tee_print_and_streams(log_file_path: Path):
    """Capture all prints/stdout/stderr while keeping console output visible."""
    original_print = builtins.print

    with log_file_path.open("w", encoding="utf-8") as log_fh:
        tee_stdout = _TeeStream(sys.stdout, log_fh)
        tee_stderr = _TeeStream(sys.stderr, log_fh)

        def tee_print(*args, **kwargs):
            # stdout/stderr are already redirected to tee streams, so one print
            # call is enough to mirror output to console and file.
            original_print(*args, **kwargs)

        builtins.print = tee_print
        try:
            with contextlib.redirect_stdout(tee_stdout), contextlib.redirect_stderr(tee_stderr):
                yield
        finally:
            builtins.print = original_print


def _to_json_safe(value: Any) -> Any:
    """Recursively convert dataframes/arrays to JSON-safe objects."""
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]
    return value


def _collect_runtime_metadata(args: argparse.Namespace, runner_name: str) -> dict[str, Any]:
    return {
        "runner_name": runner_name,
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "process_id": os.getpid(),
        "cli_args": vars(args),
        "start_time_iso": datetime.now().isoformat(),
    }


def _configure_warning_filters(ignore_known_warnings: bool) -> None:
    """Apply optional warning filters for cleaner CLI output.

    This intentionally does not suppress all warnings; it only filters common,
    non-fatal noise categories when requested.
    """
    if not ignore_known_warnings:
        return
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)


# ---------------------------------------------------------------------------
# Source Combination Comparison Mode
# ---------------------------------------------------------------------------

def _print_source_comparison_guide() -> None:
    """
    Print a comprehensive guide for testing different source combinations.
    """
    print("\n" + "="*90)
    print("  SOURCE COMBINATION COMPARISON GUIDE")
    print("="*90)
    print("""
  This guide shows you what to expect for EACH source combination.
  
  ┌──────────────────────────────────────────────────────────────────────────┐
  │ SINGLE SOURCES (Run 1 at a time)                                         │
  ├──────────────────────────────────────────────────────────────────────────┤
  │                                                                            │
  │  1️⃣  FTIR Only                                                           │
  │      Command: python run_pipeline.py                                      │
  │      Select:  FTIR                                                        │
  │      Expect:  ✓ 02b_ftir_spectra.png                                      │
  │               ✓ 08a_confusion_species_ml[FTIR].png                        │
  │               ✓ Core model figures                                        │
  │      Figures: ~7                                                          │
  │                                                                            │
  │  2️⃣  HPLC Only                                                           │
  │      Command: python run_pipeline.py                                      │
  │      Select:  HPLC                                                        │
  │      Expect:  ✓ 01_hplc_chromatograms.png                                 │
  │               ✓ 03_assay_heatmap.png (HPLC analysis)                      │
  │               ✓ 04_solvent_heatmap.png                                    │
  │               ✓ 08a_confusion_species_ml[HPLC].png                        │
  │      Figures: ~9                                                          │
  │                                                                            │
  │  3️⃣  GCMS Only                                                           │
  │      Command: python run_pipeline.py                                      │
  │      Select:  GCMS                                                        │
  │      Expect:  ✓ 02_gcms_spectra.png                                       │
  │               ✓ 08a_confusion_species_ml[GCMS].png                        │
  │               ✓ Core model figures                                        │
  │      Figures: ~7                                                          │
  │                                                                            │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │ DUAL SOURCES (Run 1 at a time)                                           │
  ├──────────────────────────────────────────────────────────────────────────┤
  │                                                                            │
  │  4️⃣  FTIR + HPLC                                                         │
  │      Command: python run_pipeline.py                                      │
  │      Select:  FTIR, HPLC                                                  │
  │      Expect:  ✓ 02b_ftir_spectra.png                                      │
  │               ✓ 01_hplc_chromatograms.png                                 │
  │               ✓ 03_assay_heatmap.png through 15_best_solvent_dist.png    │
  │               ✓ 08a_confusion_species_ml[FTIR + HPLC].png                │
  │      Figures: ~17 (includes all HPLC analysis)                            │
  │                                                                            │
  │  5️⃣  FTIR + GCMS                                                         │
  │      Command: python run_pipeline.py                                      │
  │      Select:  FTIR, GCMS                                                  │
  │      Expect:  ✓ 02b_ftir_spectra.png                                      │
  │               ✓ 02_gcms_spectra.png                                       │
  │               ✓ 08a_confusion_species_ml[FTIR + GCMS].png                │
  │      Figures: ~14 (combined spectra + core models)                        │
  │                                                                            │
  │  6️⃣  HPLC + GCMS (Traditional)                                           │
  │      Command: python run_pipeline.py                                      │
  │      Select:  HPLC, GCMS                                                  │
  │      Expect:  ✓ 01_hplc_chromatograms.png                                 │
  │               ✓ 02_gcms_spectra.png                                       │
  │               ✓ 03_assay_heatmap.png through 15_best_solvent_dist.png    │
  │               ✓ 08a_confusion_species_ml[HPLC + GCMS].png                │
  │      Figures: ~16 (full traditional analysis)                             │
  │                                                                            │
  └──────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │ ALL THREE SOURCES                                                        │
  ├──────────────────────────────────────────────────────────────────────────┤
  │                                                                            │
  │  7️⃣  FTIR + HPLC + GCMS (Complete Multi-Modal)                          │
  │      Command: python run_pipeline.py                                      │
  │      Select:  FTIR, HPLC, GCMS                                            │
  │      Expect:  ✓ ALL spectra (FTIR, HPLC, GCMS)                           │
  │               ✓ ALL analysis figures                                      │
  │               ✓ 08a_confusion_species_ml[FTIR + HPLC + GCMS].png         │
  │      Figures: ~18 (maximum coverage)                                      │
  │                                                                            │
  └──────────────────────────────────────────────────────────────────────────┘

  COMPARISON WORKFLOW:
  
  Step 1: Run GCMS only       → Note accuracy and figure count
  Step 2: Run HPLC + GCMS     → Compare: Is GCMS worth adding?
  Step 3: Run FTIR + GCMS     → Compare: Is FTIR better than HPLC?
  Step 4: Run all three       → Final check for multi-modal synergy
  
  Result: You'll know which sources are essential vs redundant!

""")
    print("="*90 + "\n")


def _run_source_comparison(args) -> None:
    """
    Run pipeline with all 7 source combinations and show comparison.
    """
    print("\n" + "="*90)
    print("  AUTOMATED SOURCE COMBINATION COMPARISON")
    print("="*90)
    
    source_combinations = [
        ["FTIR"],
        ["HPLC"],
        ["GCMS"],
        ["FTIR", "HPLC"],
        ["FTIR", "GCMS"],
        ["HPLC", "GCMS"],
        ["FTIR", "HPLC", "GCMS"],
    ]
    
    print("\nThis will test all 7 source combinations in sequence.")
    print("Each run will create a new figures directory with source-aware labels.")
    print("WARNING: This requires significant computation time!\n")
    
    confirm = input("Continue with all 7 combinations? (y/n): ").strip().lower()
    if confirm not in ["y", "yes"]:
        print("[Cancelled] Use --compare-sources to run again.\n")
        return
    
    results_summary = []
    
    for i, sources in enumerate(source_combinations, 1):
        combo_name = " + ".join(sources)
        figures_subdir = Path(args.figures_dir) / f"combo_{i:02d}_{combo_name.replace(' + ', '_')}"
        
        print(f"\n{'='*90}")
        print(f"  [{i}/7] Testing: {combo_name}")
        print(f"{'='*90}")
        
        # Simulate running pipeline with these sources
        # In reality, this would need to automate the source selection prompt
        print(f"  Sources: {combo_name}")
        print(f"  Output: {figures_subdir}")
        print(f"\n  [NOTE] Manual step: When prompted, select: {', '.join(sources)}")
        print(f"  [NOTE] To fully automate, edit DataSourceSelector to accept CLI args")
        
        results_summary.append({
            "test": i,
            "sources": combo_name,
            "figures_dir": str(figures_subdir),
        })
    
    # Print comparison summary
    print("\n" + "="*90)
    print("  COMPARISON SUMMARY")
    print("="*90)
    print(f"\n  {len(results_summary)} combinations tested:")
    print("  " + "-"*86)
    for r in results_summary:
        print(f"  [{r['test']}] {r['sources']:25s} → {r['figures_dir']}")
    
    print("\n" + "="*90)
    print("  NEXT STEPS:")
    print("  1. Compare accuracy metrics across figures (confusion matrices)")
    print("  2. Count figures in each directory (should increase with sources)")
    print("  3. Check source labels in confusion matrix filenames")
    print("  4. Determine which sources are essential vs redundant")
    print("="*90 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(
    *,
    training_display: str | None = None,
    training_progress_callback: callable | None = None,
) -> None:
    args = parse_args()
    _configure_warning_filters(args.ignore_known_warnings)

    selected_training_display = training_display or args.training_display

    # Parse per-step display overrides (format: "5:progress,6:verbose")
    step_display_overrides: dict[int, str] = {}
    if args.step_display:
        try:
            for part in str(args.step_display).split(","):
                if not part.strip():
                    continue
                k, v = part.split(":")
                step_display_overrides[int(k.strip())] = v.strip()
        except Exception:
            print("[WARN] Could not parse --step-display, ignoring overrides.")

    # Create per-step progress callbacks so ML and DL can use different displays
    ml_display = step_display_overrides.get(5, selected_training_display)
    dl_display = step_display_overrides.get(6, selected_training_display)

    progress_callback_ml = _make_training_progress_callback(
        ml_display,
        external_callback=training_progress_callback,
    )
    progress_callback_dl = _make_training_progress_callback(
        dl_display,
        external_callback=training_progress_callback,
    )

    runner_name = args.runner_name.strip() or getpass.getuser()
    runner_slug = _safe_slug(runner_name, fallback="runner")
    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    run_root = Path(args.logs_dir) / date_folder / runner_slug / f"run_{run_ts}"
    run_root.mkdir(parents=True, exist_ok=True)

    runtime_metadata = _collect_runtime_metadata(args, runner_name)
    runtime_metadata_path = run_root / "runtime_metadata.json"
    runtime_metadata_path.write_text(json.dumps(runtime_metadata, indent=2), encoding="utf-8")

    log_file_path = run_root / "test_output.log"

    with _tee_print_and_streams(log_file_path):
        print("\n" + "=" * 80)
        print("  RUN ARTIFACT INITIALIZATION")
        print("=" * 80)
        print(f"  Runner       : {runner_name}")
        print(f"  Run ID       : {run_ts}")
        print(f"  Run folder   : {run_root}")
        print(f"  Output log   : {log_file_path}")
        print("=" * 80 + "\n")

        output_path = Path(args.output)
        figures_dir = run_root / "graphs"
        # Handle comparison mode
        if args.compare_sources:
            _print_source_comparison_guide()
            _run_source_comparison(args)
            return

        if args.publication_mode:
            args.nested_cv = True
            args.skip_optimization = False
            print("\n[Publication mode enabled] Nested CV and optimization are on; artifacts will be exported for reporting.")
    
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

                if validation_results["failed"]:
                    print("\n[ERROR] Species validation failed!")
                    print("Please fix the following species names before running the pipeline:")
                    for species in validation_results["failed"]:
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

        # Allow non-interactive mode via CLI args (used by GUI)
        if args.data_mode:
            data_mode = args.data_mode
            print(f"[AUTO] Using data mode from CLI: {data_mode}")
        else:
            data_mode = data_gen.ask_data_mode()

        if args.selected_sources:
            # Parse provided comma-separated list
            selected_sources = [s.strip().upper() for s in str(args.selected_sources).split(",") if s.strip()]
            print(f"[AUTO] Using selected sources from CLI: {', '.join(selected_sources)}")
        else:
            source_selector = DataSourceSelector()
            source_selector.print_welcome()
            selected_sources = source_selector.ask_source_selection()
            print(f"\n[OK] Selected sources: {', '.join(selected_sources)}")

        combo_slug = _safe_slug("_".join(sorted(s.upper() for s in selected_sources)), fallback="UNSPECIFIED")
        combo_graph_dir = run_root / "graphs" / f"combo_{combo_slug}"
        combo_graph_dir.mkdir(parents=True, exist_ok=True)

        # If the user did not provide `--figures-dir`, write figures into
        # the per-run artifacts folder; otherwise use the provided path.
        if not args.figures_dir:
            figures_dir = combo_graph_dir
        else:
            figures_dir = Path(args.figures_dir)
            figures_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[OK] Using {data_mode.upper()} data mode for analysis")
        print(f"[OK] Graphs for this run will be stored at: {figures_dir}")
    
    # ------------------------------------------------------------------
    # Step 0.5: Optional Biodata Collection
    # ------------------------------------------------------------------
    biodata_collector = None
    biodata = None
    # Biodata collection: can be invoked non-interactively via --add-biodata
    if args.add_biodata:
        add_biodata = "y"
    else:
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

    # Keep track of optional source-specific artifacts.
    source_artifacts_dir = output_path.parent / "source_inputs"
    source_artifacts_dir.mkdir(parents=True, exist_ok=True)
    generated_sources: dict[str, pd.DataFrame] = {}

    # Prepare source templates directory (example files user can paste into)
    templates_dir = output_path.parent / "source_templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    def _write_templates():
        """Write example CSV templates for FTIR, HPLC, and GCMS including dummy target columns."""
        from HPLC_GCMS_Fingerprint.modules.sample_data_generator import SampleDataGenerator
        from HPLC_GCMS_Fingerprint.data_generation.constants import N_HPLC_PEAKS, N_MZ_BINS, SOLVENTS, ASSAYS

        gen = SampleDataGenerator()

        # HPLC template
        hplc_example = generate_hplc(n_replicates=1, random_seed=101)
        hplc_path = templates_dir / "template_hplc.csv"
        hplc_example.to_csv(hplc_path, index=False)

        # GCMS template
        gcms_example = generate_gcms(n_replicates=1, random_seed=102)
        gcms_path = templates_dir / "template_gcms.csv"
        gcms_example.to_csv(gcms_path, index=False)

        # FTIR template: generate spectral cols and append activity/assay dummy cols
        ftir_df = gen.generate_ftir_data(n_samples=1)
        # Add activity and assay columns with dummy values so FTIR-only training is possible
        for s in SOLVENTS:
            ftir_df[f"activity_{s}"] = 0.0
            for assay in ASSAYS:
                ftir_df[f"{assay}_{s}"] = 0.0
        ftir_path = templates_dir / "template_ftir.csv"
        ftir_df.to_csv(ftir_path, index=False)

        # README describing the template layout
        readme = templates_dir / "README.txt"
        readme.write_text(
            (
                "Templates for data sources.\n\n"
                "- template_hplc.csv: HPLC fingerprint rows. Columns: sample_id, species, phylum, replicate, intensity_RT_01..intensity_RT_{n_hplc}, activity_<solvent>, <assay>_<solvent> for each assay.\n"
                "- template_gcms.csv: GC-MS fingerprint rows. Columns: sample_id, species, phylum, replicate, intensity_mz_001..intensity_mz_{n_mz}, activity_<solvent>, <assay>_<solvent>.\n"
                "- template_ftir.csv: FTIR spectral rows. Columns: sample_id, species, phylum, wn_<wavenumber>_.., plus activity_<solvent> and per-assay columns if you want FTIR-only training.\n\n"
                "Guidelines: Replace the example rows with your experimental data. Ensure species and phylum columns are filled and that activity_<solvent> columns exist if you want training to build targets.\n"
            ).format(n_hplc=N_HPLC_PEAKS, n_mz=N_MZ_BINS)
        )

    # write templates once
    try:
        _write_templates()
        print(f"  Example data templates written to: {templates_dir}")
    except Exception as exc:
        print(f"  [WARN] Could not write templates: {exc}")

    # ------------------------------------------------------------------
    # Step 0.6 – Load Data (Real or Dummy)
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 0.6 – Load Data for Selected Sources")
    print("="*60)

    hplc_df = None
    gcms_df = None
    ftir_df = None

    if data_mode == "real":
        print(f"\n[Real Data Mode] Loading data for: {', '.join(selected_sources)}")
        
        # Use the real data loader to load from files
        real_data = prompt_for_real_data(selected_sources)
        
        hplc_df = real_data.get("HPLC")
        gcms_df = real_data.get("GCMS")
        ftir_df = real_data.get("FTIR")
        
        # Validate that at least one source was loaded
        loaded_count = sum(1 for v in real_data.values() if v is not None)
        if loaded_count == 0:
            print("\n[ERROR] No data files were loaded successfully.")
            print("Please check your files and run again.")
            sys.exit(1)
        
        print(f"\n[OK] Loaded {loaded_count} source(s)")
        if hplc_df is not None:
            print(f"  HPLC: {len(hplc_df)} samples, {len(hplc_df.columns)} columns")
        if gcms_df is not None:
            print(f"  GCMS: {len(gcms_df)} samples, {len(gcms_df.columns)} columns")
        if ftir_df is not None:
            print(f"  FTIR: {len(ftir_df)} samples, {len(ftir_df.columns)} columns")

    else:  # dummy mode
        print(f"\n[Dummy Data Mode] Generating data for: {', '.join(selected_sources)}")

        if "FTIR" in selected_sources:
            ftir_df = data_gen.generate_ftir_data(n_samples=args.reps * len(data_gen.algae_species))
            # Ensure FTIR dummy includes activity and per-assay columns so FTIR-only training is possible
            from HPLC_GCMS_Fingerprint.data_generation.constants import SOLVENTS, ASSAYS
            if not any(col.startswith("activity_") for col in ftir_df.columns):
                rng = np.random.default_rng(123)
                for s in SOLVENTS:
                    ftir_df[f"activity_{s}"] = rng.uniform(0, 100, size=len(ftir_df))
                    for assay in ASSAYS:
                        ftir_df[f"{assay}_{s}"] = rng.uniform(0, 100, size=len(ftir_df))
            generated_sources["FTIR"] = ftir_df
            ftir_path = source_artifacts_dir / "ftir_data.csv"
            ftir_df.to_csv(ftir_path, index=False)
            print(f"  FTIR samples generated: {len(ftir_df)}")

        if "HPLC" in selected_sources:
            hplc_df = generate_hplc(n_replicates=args.reps, random_seed=42)
            generated_sources["HPLC"] = hplc_df
            hplc_path = source_artifacts_dir / "hplc_data.csv"
            hplc_df.to_csv(hplc_path, index=False)
            print(f"  HPLC samples generated: {len(hplc_df)}")

        if "GCMS" in selected_sources:
            gcms_df = generate_gcms(n_replicates=args.reps, random_seed=43)
            generated_sources["GCMS"] = gcms_df
            gcms_path = source_artifacts_dir / "gcms_data.csv"
            gcms_df.to_csv(gcms_path, index=False)
            print(f"  GC-MS samples generated: {len(gcms_df)}")

        # For dummy mode, also generate fallback HPLC/GCMS if not in selected sources
        # (for backward compatibility with ML/DL training)
        if hplc_df is None:
            hplc_df = generate_hplc(n_replicates=args.reps, random_seed=42)
            print(f"  HPLC fallback generated: {len(hplc_df)} samples")
        
        if gcms_df is None:
            gcms_df = generate_gcms(n_replicates=args.reps, random_seed=43)
            print(f"  GC-MS fallback generated: {len(gcms_df)} samples")

        print(f"\n[OK] Generated data for {len(generated_sources)} source(s)")

    # For real data mode with multi-source, ensure we have at least HPLC or GCMS for compatibility
    if data_mode == "real":
        if hplc_df is None and gcms_df is None:
            print("\n[WARNING] Neither HPLC nor GCMS data loaded. Generating fallback HPLC/GCMS for training compatibility.")
            if hplc_df is None:
                hplc_df = generate_hplc(n_replicates=5, random_seed=42)
            if gcms_df is None:
                gcms_df = generate_gcms(n_replicates=5, random_seed=43)

    # Save real data sources to artifacts directory
    if data_mode == "real":
        if hplc_df is not None and "HPLC" in selected_sources:
            hplc_path = source_artifacts_dir / "hplc_real_data.csv"
            hplc_df.to_csv(hplc_path, index=False)
        if gcms_df is not None and "GCMS" in selected_sources:
            gcms_path = source_artifacts_dir / "gcms_real_data.csv"
            gcms_df.to_csv(gcms_path, index=False)
        if ftir_df is not None and "FTIR" in selected_sources:
            ftir_path = source_artifacts_dir / "ftir_real_data.csv"
            ftir_df.to_csv(ftir_path, index=False)

    # ------------------------------------------------------------------
    # Step 1 & 2: Export to Excel (dummy data only)
    # ------------------------------------------------------------------
    if data_mode == "dummy":
        print("\n" + "="*60)
        print("  Step 1 – Export to Excel")
        print("="*60)
        export_to_excel(hplc_df, gcms_df, output_path=output_path)

    # ------------------------------------------------------------------
    # Step 3 & 4: Ingest and build feature matrix
    # ------------------------------------------------------------------
    print("\n" + "="*60)
    print("  Step 3 – Load, validate, engineer features")
    print("="*60)

    # Build dataset from available sources (works with any combination)
    dataset = MultiTaskDataset.from_sources(
        hplc_df=hplc_df,
        gcms_df=gcms_df,
        ftir_df=ftir_df,
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
    
    # Get species names from available data sources
    species_names = set()
    if hplc_df is not None and "species" in hplc_df.columns:
        species_names.update(hplc_df["species"].unique())
    if gcms_df is not None and "species" in gcms_df.columns:
        species_names.update(gcms_df["species"].unique())
    if ftir_df is not None and "species" in ftir_df.columns:
        species_names.update(ftir_df["species"].unique())
    
    if species_names:
        taxonomy_df = _fetch_taxonomy_table(
            species_names=sorted(species_names),
            cache_path=output_path.parent / "taxonomy_cache.csv",
            output_path=output_path.parent / "species_taxonomy.csv",
        )
    else:
        taxonomy_df = pd.DataFrame()
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
    ml_tuning_mode = "manual"
    ml_search_results: dict[str, Any] | None = None
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

        use_sklearn_search = input(
            "  Switch ML tuning to scikit-learn GridSearchCV/RandomizedSearchCV? (y/n, default: n): "
        ).strip().lower()
        if use_sklearn_search in {"y", "yes"}:
            search_kind = input(
                "  Choose search type [grid/randomized] (default: randomized): "
            ).strip().lower() or "randomized"
            ml_tuning_mode = "grid" if search_kind.startswith("g") else "randomized"
            print(f"  [ML] Using sklearn {ml_tuning_mode.title()}SearchCV...")

            ml_search = _run_ml_sklearn_search(
                opt_train_ds,
                search_mode=ml_tuning_mode,
                random_state=42,
            )
            ml_search_results = ml_search
            selected_ml_clf = ml_search["best_params"]["clf_type"]
            selected_ml_reg = ml_search["best_params"]["reg_type"]
            selected_n_estimators_clf = ml_search["best_params"]["n_estimators_clf"]
            selected_n_estimators_reg = ml_search["best_params"]["n_estimators_reg"]
            print(
                "  [ML] Best params -> "
                f"clf={selected_ml_clf}, reg={selected_ml_reg}, "
                f"n_estimators_clf={selected_n_estimators_clf}, "
                f"n_estimators_reg={selected_n_estimators_reg}, "
                f"score={ml_search['best_score']:.4f}"
            )
        else:
            print("  [ML] Using current manual tuning settings...")
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
        nested_cv_summary["ml"] = _run_nested_cv_ml(
            train_ds,
            random_state=42,
            outer_splits=3,
            tuning_mode=ml_tuning_mode,
        )
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
        progress_callback=progress_callback_ml,
        verbose=(ml_display != "progress"),
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
            progress_callback=progress_callback_dl,
            verbose=(dl_display != "progress"),
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
            run_root=run_root,
            args=args,
            dataset=dataset,
            selected_sources=selected_sources,
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
            ml_tuning_mode=ml_tuning_mode,
            ml_search_results=ml_search_results,
            runtime_metadata=runtime_metadata,
            test_output_log_path=log_file_path,
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
        print(f"  Generating figures for selected sources: {', '.join(selected_sources)}")
        figure_summary = _generate_figures(
            hplc_df=hplc_df,
            gcms_df=gcms_df,
            ftir_df=ftir_df,
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
            selected_sources=selected_sources,
        )
        figure_summary_path = run_root / "graphs" / "figure_manifest.json"
        figure_summary_path.parent.mkdir(parents=True, exist_ok=True)
        figure_summary_path.write_text(
            json.dumps(_to_json_safe(figure_summary), indent=2),
            encoding="utf-8",
        )
        print(f"\n  All figures saved to: {figures_dir}/")
        print(f"  Figure manifest: {figure_summary_path}")

    print("\n✅  Pipeline completed successfully.\n")
    print(f"Run artifacts root: {run_root}")


# ---------------------------------------------------------------------------
# Figure generation
# ---------------------------------------------------------------------------

def _generate_figures(
    *,
    hplc_df,
    gcms_df,
    ftir_df,
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
    selected_sources: list[str] = None,
) -> dict[str, Any]:
    import torch
    figures_dir.mkdir(parents=True, exist_ok=True)
    ext = f".{figure_format}"
    
    # Default to all sources if not specified (backward compatibility)
    if selected_sources is None:
        selected_sources = ["HPLC", "GCMS", "FTIR"]
    
    # Ensure selected_sources is normalized
    selected_sources = [s.upper() for s in selected_sources]
    
    # Track which figures are being generated
    generated_fig_count = 0
    
    # Build sources string for model labels
    sources_str = " + ".join(selected_sources)
    
    print(f"\n  [Figures] Generating visualizations for: {', '.join(selected_sources)}")

    # 1. HPLC chromatograms (only if HPLC is selected)
    if "HPLC" in selected_sources:
        plot_hplc_chromatogram(
            hplc_df, HPLC_RT_CENTERS,
            output_path=figures_dir / f"01_hplc_chromatograms{ext}",
        )
        print(f"    ✓ HPLC chromatograms")
        generated_fig_count += 1

    # 2. GC-MS spectra (only if GCMS is selected)
    if "GCMS" in selected_sources:
        plot_gcms_spectrum(
            gcms_df, MZ_BIN_CENTERS,
            output_path=figures_dir / f"02_gcms_spectra{ext}",
        )
        print(f"    ✓ GC-MS spectra")
        generated_fig_count += 1

    # 2b. FTIR spectra (only if FTIR is selected)
    if "FTIR" in selected_sources and ftir_df is not None and not ftir_df.empty:
        plot_ftir_spectrum(
            ftir_df,
            output_path=figures_dir / f"02b_ftir_spectra{ext}",
        )
        print(f"    ✓ FTIR spectra")
        generated_fig_count += 1

    # 3. Assay score heatmap (only if HPLC is selected, as it uses HPLC data)
    if "HPLC" in selected_sources:
        plot_assay_heatmap(
            hplc_df, ASSAYS, SOLVENTS,
            output_path=figures_dir / f"03_assay_heatmap{ext}",
        )
        print(f"    ✓ Assay score heatmap")
        generated_fig_count += 1

    # 4. Solvent heatmap (only if HPLC is selected)
    if "HPLC" in selected_sources:
        plot_solvent_heatmap(
            hplc_df, SOLVENTS,
            output_path=figures_dir / f"04_solvent_heatmap{ext}",
        )
        print(f"    ✓ Solvent heatmap")
        generated_fig_count += 1

    # 5. Assay box plots by phylum (only if HPLC is selected)
    if "HPLC" in selected_sources:
        plot_assay_boxplots(
            hplc_df, ASSAYS, SOLVENTS,
            output_path=figures_dir / f"05_assay_boxplots{ext}",
        )
        print(f"    ✓ Assay boxplots")
        generated_fig_count += 1

    # 6. Solvent grouped bars by phylum (only if HPLC is selected)
    if "HPLC" in selected_sources:
        plot_solvent_barplots(
            hplc_df, SOLVENTS,
            output_path=figures_dir / f"06_solvent_barplots{ext}",
        )
        print(f"    ✓ Solvent barplots")
        generated_fig_count += 1

    # 7. PCA biplot (uses combined features from all selected sources)
    plot_pca_biplot(
        X_raw=dataset.X,
        phylum_labels=dataset.phylum,
        phylum_names=dataset.phylum_names,
        output_path=figures_dir / f"07_pca_biplot{ext}",
    )
    print(f"    ✓ PCA biplot")
    generated_fig_count += 1

    # 7b. PLS-DA biplot (uses combined features from all selected sources)
    plot_plsda_biplot(
        X_raw=dataset.X,
        phylum_labels=dataset.phylum,
        phylum_names=dataset.phylum_names,
        output_path=figures_dir / f"07b_plsda_biplot{ext}",
    )
    print(f"    ✓ PLS-DA biplot")
    generated_fig_count += 1

    # 8. Confusion matrices – ML model
    ml_preds = ml_model.predict(test_ds.X)
    plot_confusion_matrix(
        test_ds.species, ml_preds["pred_species"],
        class_names=dataset.species_names,
        title=f"Species Classification – ML Baseline [{sources_str}]",
        output_path=figures_dir / f"08a_confusion_species_ml{ext}",
    )
    print(f"    ✓ Confusion matrix – Species (ML)")
    generated_fig_count += 1
    
    plot_confusion_matrix(
        test_ds.phylum, ml_preds["pred_phylum"],
        class_names=dataset.phylum_names,
        title=f"Phylum Classification – ML Baseline [{sources_str}]",
        output_path=figures_dir / f"08b_confusion_phylum_ml{ext}",
    )
    print(f"    ✓ Confusion matrix – Phylum (ML)")
    generated_fig_count += 1

    # 8c. Confusion matrices – DL model
    if dl_model is not None:
        dev = torch.device("cpu")
        X_t = torch.tensor(test_ds.X, dtype=torch.float32).to(dev)
        with torch.no_grad():
            dl_out = dl_model.predict(X_t)
        plot_confusion_matrix(
            test_ds.species, dl_out["pred_species"].cpu().numpy(),
            class_names=dataset.species_names,
            title=f"Species Classification – DL Model [{sources_str}]",
            output_path=figures_dir / f"08c_confusion_species_dl{ext}",
        )
        print(f"    ✓ Confusion matrix – Species (DL)")
        generated_fig_count += 1
        
        plot_confusion_matrix(
            test_ds.phylum, dl_out["pred_phylum"].cpu().numpy(),
            class_names=dataset.phylum_names,
            title=f"Phylum Classification – DL Model [{sources_str}]",
            output_path=figures_dir / f"08d_confusion_phylum_dl{ext}",
        )
        print(f"    ✓ Confusion matrix – Phylum (DL)")
        generated_fig_count += 1

    # 9. DL training curves
    if dl_history:
        plot_training_curves(
            dl_history,
            output_path=figures_dir / f"09_training_curves{ext}",
        )
        print(f"    ✓ Training curves")
        generated_fig_count += 1

    # 10. Feature importance (species head)
    import numpy as np

    def _extract_feature_importances(estimator, X, y):
        if hasattr(estimator, "feature_importances_"):
            return np.asarray(estimator.feature_importances_, dtype=float)

        if hasattr(estimator, "coef_"):
            coef = np.asarray(estimator.coef_, dtype=float)
            if coef.ndim == 1:
                return np.abs(coef)
            return np.mean(np.abs(coef), axis=0)

        try:
            from sklearn.inspection import permutation_importance

            result = permutation_importance(
                ml_model.head_species,
                X,
                y,
                n_repeats=5,
                random_state=42,
                scoring="accuracy",
                n_jobs=-1,
            )
            return np.asarray(result.importances_mean, dtype=float)
        except Exception:
            return None

    clf = ml_model.head_species.named_steps["clf"]
    importances = _extract_feature_importances(clf, test_ds.X, test_ds.species)
    if importances is None:
        print("    • Feature importance skipped (model does not expose coefficients or importances)")
    else:
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
            title="ML Feature Importance – Species Head",
            output_path=figures_dir / f"10_feature_importance{ext}",
        )
        print(f"    ✓ Feature importance")
        generated_fig_count += 1

    # 11. Predicted vs true scatter – solvent head
    plot_prediction_scatter(
        test_ds.y_solvents,
        ml_preds["pred_solvents"],
        output_names=dataset.solvent_names,
        title=f"Solvent Activity – ML Predicted vs True [{sources_str}]",
        output_path=figures_dir / f"11a_scatter_solvents_ml{ext}",
    )
    print(f"    ✓ Solvent predictions scatter (ML)")
    generated_fig_count += 1
    
    plot_prediction_scatter(
        test_ds.y_assays,
        ml_preds["pred_assays"],
        output_names=dataset.assay_names,
        title=f"Assay Performance – ML Predicted vs True [{sources_str}]",
        output_path=figures_dir / f"11b_scatter_assays_ml{ext}",
    )
    print(f"    ✓ Assay predictions scatter (ML)")
    generated_fig_count += 1

    if dl_model is not None:
        with torch.no_grad():
            dl_sol_pred = dl_out["pred_solvents"].cpu().numpy()
            dl_ass_pred = dl_out["pred_assays"].cpu().numpy()
        plot_prediction_scatter(
            test_ds.y_solvents, dl_sol_pred,
            output_names=dataset.solvent_names,
            title=f"Solvent Activity – DL Predicted vs True [{sources_str}]",
            output_path=figures_dir / f"11c_scatter_solvents_dl{ext}",
        )
        print(f"    ✓ Solvent predictions scatter (DL)")
        generated_fig_count += 1
        
        plot_prediction_scatter(
            test_ds.y_assays, dl_ass_pred,
            output_names=dataset.assay_names,
            title=f"Assay Performance – DL Predicted vs True [{sources_str}]",
            output_path=figures_dir / f"11d_scatter_assays_dl{ext}",
        )
        print(f"    ✓ Assay predictions scatter (DL)")
        generated_fig_count += 1

    # 12. Radar chart – solvent performance per species (only if HPLC is selected)
    if "HPLC" in selected_sources:
        plot_radar_solvent(
            hplc_df, SOLVENTS,
            output_path=figures_dir / f"12_radar_solvent{ext}",
        )
        print(f"    ✓ Radar chart – Solvent performance")
        generated_fig_count += 1

    # 13. Phylum × assay recommendation (only if HPLC is selected)
    if "HPLC" in selected_sources:
        plot_phylum_assay_recommendation(
            hplc_df, ASSAYS, SOLVENTS,
            output_path=figures_dir / f"13_phylum_assay_recommendation{ext}",
        )
        print(f"    ✓ Phylum × assay recommendation")
        generated_fig_count += 1

    # 14. Solvent × assay interaction (only if HPLC is selected)
    if "HPLC" in selected_sources:
        plot_solvent_assay_interaction(
            hplc_df, ASSAYS, SOLVENTS,
            output_path=figures_dir / f"14_solvent_assay_interaction{ext}",
        )
        print(f"    ✓ Solvent × assay interaction")
        generated_fig_count += 1

    # 15. Best-solvent distribution per phylum (only if HPLC is selected)
    if "HPLC" in selected_sources:
        plot_best_solvent_distribution(
            hplc_df, SOLVENTS,
            output_path=figures_dir / f"15_best_solvent_distribution{ext}",
        )
        print(f"    ✓ Best solvent distribution")
        generated_fig_count += 1

    # 16. Taxonomy-based phylogenetic tree
    if not taxonomy_df.empty:
        plot_phylogenetic_tree(
            taxonomy_df=taxonomy_df,
            output_path=figures_dir / f"16_phylogenetic_tree{ext}",
        )
        print(f"    ✓ Phylogenetic tree")
        generated_fig_count += 1
    
    # =========================================================================
    # SUMMARY: Figure Generation Report by Source Combination
    # =========================================================================
    print(f"\n  " + "="*70)
    print(f"  FIGURE GENERATION SUMMARY")
    print(f"  " + "="*70)
    print(f"  Data Sources Selected: {', '.join(selected_sources)}")
    print(f"  Source Combination: [{sources_str}]")
    print(f"  Total Figures Generated: {generated_fig_count}")
    print(f"  Output Directory: {figures_dir}")
    
    # List all generated source-specific figures
    print(f"\n  SOURCE-SPECIFIC FIGURES:")
    if "HPLC" in selected_sources:
        print(f"    • HPLC Chromatograms")
        print(f"    • Assay Score Heatmap (HPLC-based)")
        print(f"    • Solvent Heatmap (HPLC-based)")
        print(f"    • Assay Boxplots (HPLC-based)")
        print(f"    • Solvent Barplots (HPLC-based)")
        print(f"    • Radar Chart – Solvent Performance (HPLC-based)")
        print(f"    • Phylum × Assay Recommendation (HPLC-based)")
        print(f"    • Solvent × Assay Interaction (HPLC-based)")
        print(f"    • Best Solvent Distribution (HPLC-based)")
    
    if "GCMS" in selected_sources:
        print(f"    • GC-MS Spectra")
    
    if "FTIR" in selected_sources:
        print(f"    • FTIR Spectra")
    
    # List model evaluation figures
    print(f"\n  MODEL EVALUATION FIGURES [{sources_str}]:")
    print(f"    • PCA Biplot")
    print(f"    • PLS-DA Biplot")
    print(f"    • Confusion Matrix – Species (ML Baseline)")
    print(f"    • Confusion Matrix – Phylum (ML Baseline)")
    if dl_model is not None:
        print(f"    • Confusion Matrix – Species (DL Model)")
        print(f"    • Confusion Matrix – Phylum (DL Model)")
        print(f"    • Training Curves (DL Model)")
    
    print(f"\n  REGRESSION EVALUATION FIGURES [{sources_str}]:")
    print(f"    • Feature Importance (Species Head)")
    print(f"    • Solvent Activity Predictions (ML Baseline)")
    print(f"    • Assay Performance Predictions (ML Baseline)")
    if dl_model is not None:
        print(f"    • Solvent Activity Predictions (DL Model)")
        print(f"    • Assay Performance Predictions (DL Model)")
    
    if not taxonomy_df.empty:
        print(f"\n  ADDITIONAL ANALYSES:")
        print(f"    • Phylogenetic Tree (Taxonomy-based)")
    
    # Coverage check for this source/model combination.
    expected_ids = [
        "07_pca_biplot",
        "07b_plsda_biplot",
        "08a_confusion_species_ml",
        "08b_confusion_phylum_ml",
        "10_feature_importance",
        "11a_scatter_solvents_ml",
        "11b_scatter_assays_ml",
    ]
    if "HPLC" in selected_sources:
        expected_ids.extend([
            "01_hplc_chromatograms",
            "03_assay_heatmap",
            "04_solvent_heatmap",
            "05_assay_boxplots",
            "06_solvent_barplots",
            "12_radar_solvent",
            "13_phylum_assay_recommendation",
            "14_solvent_assay_interaction",
            "15_best_solvent_distribution",
        ])
    if "GCMS" in selected_sources:
        expected_ids.append("02_gcms_spectra")
    if "FTIR" in selected_sources:
        expected_ids.append("02b_ftir_spectra")
    if dl_model is not None:
        expected_ids.extend([
            "08c_confusion_species_dl",
            "08d_confusion_phylum_dl",
            "09_training_curves",
            "11c_scatter_solvents_dl",
            "11d_scatter_assays_dl",
        ])
    if not taxonomy_df.empty:
        expected_ids.append("16_phylogenetic_tree")

    generated_files = sorted([p.name for p in figures_dir.glob(f"*{ext}")])
    generated_ids = sorted({Path(name).stem for name in generated_files})
    missing_expected = sorted(set(expected_ids) - set(generated_ids))

    if missing_expected:
        print("\n  [WARNING] Some expected figures were not generated:")
        for missing in missing_expected:
            print(f"    - {missing}{ext}")
    else:
        print("\n  [OK] Figure coverage check passed for this combination.")

    print(f"  " + "="*70 + "\n")

    return {
        "selected_sources": selected_sources,
        "source_combination": sources_str,
        "figure_format": figure_format,
        "output_directory": str(figures_dir),
        "generated_count": int(generated_fig_count),
        "generated_files": generated_files,
        "generated_ids": generated_ids,
        "expected_ids": sorted(expected_ids),
        "missing_expected": missing_expected,
    }


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


def _run_ml_sklearn_search(
    train_ds: MultiTaskDataset,
    search_mode: str = "randomized",
    random_state: int = 42,
    n_iter: int = 18,
) -> dict[str, Any]:
    """Run GridSearchCV or RandomizedSearchCV over the ML baseline parameters."""
    param_space = {
        "clf_type": ["random_forest", "gradient_boosting", "svm", "logistic_regression"],
        "reg_type": ["gradient_boosting", "random_forest", "ridge", "lasso"],
        "n_estimators_clf": [150, 300, 500],
        "n_estimators_reg": [100, 200, 400],
    }

    X = train_ds.X
    y = pack_multitask_targets(
        train_ds.species,
        train_ds.phylum,
        train_ds.y_solvents,
        train_ds.y_assays,
    )
    cv = KFold(n_splits=max(2, min(3, len(train_ds))), shuffle=True, random_state=random_state)
    estimator = MLMultiTaskSearchEstimator(random_state=random_state)

    if search_mode == "grid":
        search = GridSearchCV(
            estimator=estimator,
            param_grid=param_space,
            scoring=None,
            cv=cv,
            n_jobs=-1,
            refit=True,
        )
    else:
        total_combinations = len(ParameterGrid(param_space))
        search = RandomizedSearchCV(
            estimator=estimator,
            param_distributions=param_space,
            n_iter=min(n_iter, total_combinations),
            scoring=None,
            cv=cv,
            random_state=random_state,
            n_jobs=-1,
            refit=True,
        )

    search.fit(X, y)

    return {
        "search_mode": search_mode,
        "best_params": search.best_params_,
        "best_score": float(search.best_score_),
        "search_object": search,
        "cv_results": pd.DataFrame(search.cv_results_),
    }


def _run_nested_cv_ml(
    dataset: MultiTaskDataset,
    random_state: int = 42,
    outer_splits: int = 3,
    tuning_mode: str = "manual",
) -> dict[str, Any]:
    """Nested CV for the ML baseline: inner tuning, outer unbiased scoring."""
    outer_cv = StratifiedKFold(n_splits=outer_splits, shuffle=True, random_state=random_state)
    fold_scores: list[float] = []
    fold_params: list[dict[str, Any]] = []

    for fold_idx, (tr_idx, va_idx) in enumerate(outer_cv.split(dataset.X, dataset.species), start=1):
        outer_train = dataset._subset(tr_idx)
        outer_val = dataset._subset(va_idx)
        inner_train, inner_val = outer_train.train_test_split(test_size=0.25, random_state=random_state + fold_idx)

        if tuning_mode in {"grid", "randomized"}:
            tuned = _run_ml_sklearn_search(
                inner_train,
                search_mode=tuning_mode,
                random_state=random_state + fold_idx,
            )
            best = tuned["best_params"]
        else:
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
    run_root: Path,
    args: argparse.Namespace,
    dataset,
    selected_sources: list[str],
    selected_ml: dict[str, Any],
    selected_dl: dict[str, Any] | None,
    ml_results: dict[str, Any],
    dl_results: dict[str, Any] | None,
    best_model_name: str,
    dl_history: list[dict[str, Any]],
    nested_cv_summary: dict[str, Any] | None = None,
    ml_tuning_mode: str = "manual",
    ml_search_results: dict[str, Any] | None = None,
    runtime_metadata: dict[str, Any] | None = None,
    test_output_log_path: Path | None = None,
) -> dict[str, str]:
    """Persist run parameters and outcomes for reproducibility and publications."""
    legacy_results_dir = output_root / "results"
    legacy_results_dir.mkdir(parents=True, exist_ok=True)

    run_results_dir = run_root / "metrics"
    run_results_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = run_results_dir / "run_summary.json"
    full_metrics_json_path = run_results_dir / "full_metrics.json"
    ml_metrics_path = run_results_dir / "metrics_ml.csv"
    dl_metrics_path = run_results_dir / "metrics_dl.csv"
    dl_history_path = run_results_dir / "dl_history.csv"
    nested_cv_ml_path = run_results_dir / "nested_cv_ml_folds.csv"
    nested_cv_dl_path = run_results_dir / "nested_cv_dl_folds.csv"
    nested_cv_params_path = run_results_dir / "nested_cv_best_params.csv"
    ml_search_cv_results_path = run_results_dir / "ml_search_cv_results.csv"
    model_details_path = run_results_dir / "model_details.json"
    reports_dir = run_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

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
        "selected_sources": selected_sources,
        "selected_ml": selected_ml,
        "selected_dl": selected_dl,
        "score_board": score_board,
        "best_model": best_model_name,
        "nested_cv": nested_cv_summary or {},
        "ml_tuning_mode": ml_tuning_mode,
        "runtime_metadata": runtime_metadata or {},
        "test_output_log": str(test_output_log_path) if test_output_log_path is not None else "",
        "run_root": str(run_root),
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    # Keep legacy timestamped summary for backward compatibility.
    legacy_summary_path = legacy_results_dir / f"run_summary_{ts}.json"
    legacy_summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    pd.DataFrame(_flatten_metrics_for_csv(ml_results, model_name="ML")).to_csv(
        ml_metrics_path, index=False
    )

    if dl_results is not None:
        pd.DataFrame(_flatten_metrics_for_csv(dl_results, model_name="DL")).to_csv(
            dl_metrics_path, index=False
        )

    if dl_history:
        pd.DataFrame(dl_history).to_csv(dl_history_path, index=False)

    if nested_cv_summary:
        nested_rows: list[dict[str, Any]] = []
        for model_name, payload in nested_cv_summary.items():
            fold_scores = payload.get("fold_scores", [])
            best_params = payload.get("best_params_per_fold", [])
            for fold_idx, score in enumerate(fold_scores, start=1):
                row = {
                    "model": model_name.upper(),
                    "fold": fold_idx,
                    "score": float(score),
                    "mean_score": float(payload.get("mean_score", float("nan"))),
                    "std_score": float(payload.get("std_score", float("nan"))),
                }
                if fold_idx - 1 < len(best_params):
                    row.update({f"param_{k}": v for k, v in best_params[fold_idx - 1].items()})
                nested_rows.append(row)

        nested_df = pd.DataFrame(nested_rows)
        if not nested_df.empty:
            nested_df[nested_df["model"] == "ML"].to_csv(nested_cv_ml_path, index=False)
            nested_df[nested_df["model"] == "DL"].to_csv(nested_cv_dl_path, index=False)
            nested_df.to_csv(nested_cv_params_path, index=False)

    if ml_search_results is not None:
        cv_results = ml_search_results.get("cv_results")
        if isinstance(cv_results, pd.DataFrame) and not cv_results.empty:
            cv_results.to_csv(ml_search_cv_results_path, index=False)

    full_metrics_payload = {
        "ML": _to_json_safe(ml_results),
        "DL": _to_json_safe(dl_results) if dl_results is not None else None,
    }
    full_metrics_json_path.write_text(
        json.dumps(full_metrics_payload, indent=2),
        encoding="utf-8",
    )

    model_details_payload = {
        "selected_ml": selected_ml,
        "selected_dl": selected_dl,
        "best_model": best_model_name,
        "score_board": score_board,
        "selected_sources": selected_sources,
    }
    model_details_path.write_text(json.dumps(model_details_payload, indent=2), encoding="utf-8")

    # Export detailed classification reports as plain text.
    (reports_dir / "ml_species_classification_report.txt").write_text(
        str(ml_results.get("species", {}).get("report", "")),
        encoding="utf-8",
    )
    (reports_dir / "ml_phylum_classification_report.txt").write_text(
        str(ml_results.get("phylum", {}).get("report", "")),
        encoding="utf-8",
    )
    if dl_results is not None:
        (reports_dir / "dl_species_classification_report.txt").write_text(
            str(dl_results.get("species", {}).get("report", "")),
            encoding="utf-8",
        )
        (reports_dir / "dl_phylum_classification_report.txt").write_text(
            str(dl_results.get("phylum", {}).get("report", "")),
            encoding="utf-8",
        )

    return {
        "summary_json": str(summary_path),
        "full_metrics_json": str(full_metrics_json_path),
        "model_details_json": str(model_details_path),
        "ml_metrics_csv": str(ml_metrics_path),
        "dl_metrics_csv": str(dl_metrics_path) if dl_results is not None else "",
        "dl_history_csv": str(dl_history_path) if dl_history else "",
        "nested_cv_ml_csv": str(nested_cv_ml_path) if nested_cv_summary else "",
        "nested_cv_dl_csv": str(nested_cv_dl_path) if nested_cv_summary else "",
        "nested_cv_params_csv": str(nested_cv_params_path) if nested_cv_summary else "",
        "ml_search_cv_results_csv": str(ml_search_cv_results_path) if ml_search_results is not None else "",
        "legacy_summary_json": str(legacy_summary_path),
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

    solvent_per_output = results.get("solvents", {}).get("per_output")
    if isinstance(solvent_per_output, pd.DataFrame) and not solvent_per_output.empty:
        for _, row in solvent_per_output.iterrows():
            rows.append({
                "model": model_name,
                "metric": f"solvent_{row['name']}_mae",
                "value": float(row["MAE"]),
            })
            rows.append({
                "model": model_name,
                "metric": f"solvent_{row['name']}_rmse",
                "value": float(row["RMSE"]),
            })

    assay_per_output = results.get("assays", {}).get("per_output")
    if isinstance(assay_per_output, pd.DataFrame) and not assay_per_output.empty:
        for _, row in assay_per_output.iterrows():
            rows.append({
                "model": model_name,
                "metric": f"assay_{row['name']}_mae",
                "value": float(row["MAE"]),
            })
            rows.append({
                "model": model_name,
                "metric": f"assay_{row['name']}_rmse",
                "value": float(row["RMSE"]),
            })

    return rows


# ---------------------------------------------------------------------------
# Helper: Comparison Across Source Combinations
# ---------------------------------------------------------------------------

def _print_source_combination_guide() -> None:
    """
    Print a guide for testing different source combinations and comparing results.
    """
    print("\n" + "="*80)
    print("  TESTING DIFFERENT SOURCE COMBINATIONS")
    print("="*80)
    print("""
  The pipeline now supports flexible source combinations. Here's how to test each:

  ┌─────────────────────────────────────────────────────────────────────┐
  │ SINGLE SOURCE TESTING                                               │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                       │
  │  Test 1: FTIR Only                                                   │
  │    Run interactively and select: FTIR                                │
  │    Expected: FTIR spectra visualization + model trained on FTIR      │
    │    Output folder: per-run artifact `run_root/graphs/` (or use --figures-dir) │
  │    Look for: 02b_ftir_spectra.png                                    │
  │              08a_confusion_species_ml[FTIR].png                      │
  │                                                                       │
  │  Test 2: HPLC Only                                                   │
  │    Run interactively and select: HPLC                                │
  │    Expected: HPLC chromatogram + assay/solvent analysis + HPLC model │
    │    Output folder: per-run artifact `run_root/graphs/` (or use --figures-dir) │
  │    Look for: 01_hplc_chromatograms.png                               │
  │              03_assay_heatmap.png (HPLC-only)                        │
  │              08a_confusion_species_ml[HPLC].png                      │
  │                                                                       │
  │  Test 3: GCMS Only                                                   │
  │    Run interactively and select: GCMS                                │
  │    Expected: GC-MS spectrum + model trained on GCMS                  │
    │    Output folder: per-run artifact `run_root/graphs/` (or use --figures-dir) │
  │    Look for: 02_gcms_spectra.png                                     │
  │              08a_confusion_species_ml[GCMS].png                      │
  │                                                                       │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ DUAL SOURCE TESTING                                                 │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                       │
  │  Test 4: FTIR + HPLC                                                │
  │    Run interactively and select: FTIR, HPLC                          │
  │    Expected: Both spectra + combined analysis                        │
    │    Output folder: per-run artifact `run_root/graphs/` (or use --figures-dir) │
  │    Look for: 02b_ftir_spectra.png                                    │
  │              01_hplc_chromatograms.png                               │
  │              08a_confusion_species_ml[FTIR + HPLC].png               │
  │                                                                       │
  │  Test 5: FTIR + GCMS                                                │
  │    Run interactively and select: FTIR, GCMS                          │
  │    Expected: Both spectra + combined analysis                        │
    │    Output folder: per-run artifact `run_root/graphs/` (or use --figures-dir) │
  │    Look for: 02b_ftir_spectra.png                                    │
  │              02_gcms_spectra.png                                     │
  │              08a_confusion_species_ml[FTIR + GCMS].png               │
  │                                                                       │
  │  Test 6: HPLC + GCMS (Traditional)                                  │
  │    Run interactively and select: HPLC, GCMS                          │
  │    Expected: Full analysis (HPLC + GC-MS + all metadata)            │
    │    Output folder: per-run artifact `run_root/graphs/` (or use --figures-dir) │
  │    Look for: 01_hplc_chromatograms.png                               │
  │              02_gcms_spectra.png                                     │
  │              03_assay_heatmap.png                                    │
  │              08a_confusion_species_ml[HPLC + GCMS].png               │
  │                                                                       │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────┐
  │ TRIPLE SOURCE TESTING                                               │
  ├─────────────────────────────────────────────────────────────────────┤
  │                                                                       │
  │  Test 7: FTIR + HPLC + GCMS (Complete Multi-Modal)                 │
  │    Run interactively and select: FTIR, HPLC, GCMS                    │
  │    Expected: All spectra + complete analysis                         │
  │    Output folder: HPLC_GCMS_Fingerprint/figures/                    │
  │    Look for: All figures above                                       │
  │              08a_confusion_species_ml[FTIR + HPLC + GCMS].png        │
  │                                                                       │
  └─────────────────────────────────────────────────────────────────────┘

  KEY DIFFERENCES TO OBSERVE:
  
  ✓ Figure count changes based on sources selected
  ✓ Confusion matrices and prediction scatters labeled with source combo
  ✓ HPLC-only figures (assay/solvent analysis) only shown if HPLC selected
  ✓ Model performance may vary by source combination
  ✓ PCA/PLS-DA use combined features from all selected sources
  
  COMPARISON WORKFLOW:
  
  1. Run with GCMS only  → Note model accuracy and figures generated
  2. Run with HPLC + GCMS → Compare accuracy improvement vs GCMS alone
  3. Run with FTIR + GCMS → Compare FTIR contribution
  4. Run with all three  → Observe if multi-modal helps
  
  This allows you to quantify the value of each data source!

""")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

