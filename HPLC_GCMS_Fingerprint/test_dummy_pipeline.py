#!/usr/bin/env python
# ============================================================
# TEST SCRIPT: Dummy Data Generation & Pipeline Test
# ============================================================
"""
Quick test script to demonstrate dummy data generation
and full pipeline execution.

Usage:
    python test_dummy_pipeline.py
"""

import sys
from pathlib import Path

# Add project root to path
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from HPLC_GCMS_Fingerprint.modules.sample_data_generator import SampleDataGenerator
from HPLC_GCMS_Fingerprint.enhanced_pipeline import EnhancedPipelineOrchestrator


def main():
    """Run a quick test of the pipeline with dummy data."""
    
    print("\n" + "#"*70)
    print("#  QUICK TEST: DUMMY DATA PIPELINE")
    print("#"*70)
    
    # Create orchestrator
    output_dir = Path("test_output")
    print(f"\nTest output directory: {output_dir}")
    
    orchestrator = EnhancedPipelineOrchestrator(output_root=output_dir)
    
    # Generate dummy data
    print("\n" + "="*70)
    print("GENERATING DUMMY DATA")
    print("="*70)
    
    gen = SampleDataGenerator(random_seed=42)
    
    # Generate data
    n_samples = 15
    ftir_data = gen.generate_ftir_data(n_samples=n_samples)
    hplc_data = gen.generate_hplc_data(n_samples=n_samples)
    gcms_data = gen.generate_gcms_data(n_samples=n_samples)
    
    # Store in orchestrator
    orchestrator.sample_data = {
        "FTIR": ftir_data,
        "HPLC": hplc_data,
        "GCMS": gcms_data
    }
    orchestrator.data_mode = "dummy"
    
    # Save sample data
    orchestrator._save_sample_data()
    
    # Print summaries
    print("\n" + "-"*70)
    gen.print_data_summary(ftir_data, "FTIR")
    gen.print_data_summary(hplc_data, "HPLC")
    gen.print_data_summary(gcms_data, "GC-MS")
    
    # Step 1: Load data
    print("\n" + "="*70)
    print("STEP 1: DATA SELECTION")
    print("="*70)
    
    orchestrator.data_loader = None
    selected_sources = list(orchestrator.sample_data.keys())
    
    from HPLC_GCMS_Fingerprint.modules.data_input_validator import MultiSourceDataLoader
    orchestrator.data_loader = MultiSourceDataLoader(selected_sources)
    orchestrator.data_loader.data = orchestrator.sample_data
    
    print(f"\n[OK] Selected sources: {', '.join(selected_sources)}")
    
    # Step 2: Skip biodata collection (optional)
    print("\n" + "="*70)
    print("STEP 2: BIODATA COLLECTION (SKIPPED)")
    print("="*70)
    print("\nSkipping optional biodata collection for quick test...")
    
    # Step 3: Skip taxonomy fetching
    print("\n" + "="*70)
    print("STEP 3: NCBI TAXONOMY FETCHING (SKIPPED)")
    print("="*70)
    print("\nSkipping NCBI taxonomy fetching...")
    
    # Step 4: Make predictions
    print("\n" + "="*70)
    print("STEP 4: SPECIES PREDICTIONS & ANALYSIS")
    print("="*70)
    
    orchestrator.step4_make_predictions()
    
    # Step 5: Generate insights
    print("\n" + "="*70)
    print("STEP 5: AUTOMATED INSIGHTS")
    print("="*70)
    
    orchestrator.step5_generate_insights()
    
    # Summary
    print("\n" + "#"*70)
    print("#  TEST COMPLETE")
    print("#"*70)
    
    print(f"\n[OK] Test pipeline completed successfully!")
    print(f"[OK] Output files saved to: {output_dir}/")
    print(f"\nGenerated files:")
    
    for file_path in sorted(output_dir.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(output_dir)
            print(f"  - {rel_path}")
    
    # Display predictions summary
    if orchestrator.predictions_df is not None:
        print("\n" + "="*70)
        print("PREDICTIONS SUMMARY")
        print("="*70)
        print(f"\n{orchestrator.predictions_df.to_string()}")
    
    print("\n" + "#"*70)
    print("[OK] Test pipeline ready for demonstration!")
    print("#"*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
