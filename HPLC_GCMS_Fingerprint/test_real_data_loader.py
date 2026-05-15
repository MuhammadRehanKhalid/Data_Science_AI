"""
Quick validation test for the multi-source real data loading.
Verifies that the RealDataLoader and run_pipeline integration works correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from HPLC_GCMS_Fingerprint.modules.real_data_loader import RealDataLoader, FINGERPRINT_SPECS

def test_real_data_loader_initialization():
    """Test that RealDataLoader can be initialized with different source combinations."""
    print("\n" + "="*70)
    print("TEST 1: RealDataLoader Initialization")
    print("="*70)
    
    test_cases = [
        ["FTIR"],
        ["HPLC"],
        ["GCMS"],
        ["FTIR", "HPLC"],
        ["HPLC", "GCMS"],
        ["FTIR", "GCMS"],
        ["FTIR", "HPLC", "GCMS"],
    ]
    
    for sources in test_cases:
        try:
            loader = RealDataLoader(sources)
            print(f"✓ {', '.join(sources):30s} – OK")
        except Exception as e:
            print(f"✗ {', '.join(sources):30s} – FAILED: {e}")
            return False
    
    return True

def test_fingerprint_specs():
    """Test that all fingerprint specs are properly defined."""
    print("\n" + "="*70)
    print("TEST 2: Fingerprint Specifications")
    print("="*70)
    
    for source, spec in FINGERPRINT_SPECS.items():
        print(f"\n{source}:")
        print(f"  Name:       {spec['name']}")
        print(f"  Pattern:    {spec['feature_pattern']}")
        print(f"  Metadata:   {', '.join(spec['metadata_cols'])}")
        print(f"  Example:    {spec['example']}")
    
    return True

def test_imports():
    """Test that all necessary imports work."""
    print("\n" + "="*70)
    print("TEST 3: Import Integration")
    print("="*70)
    
    try:
        from HPLC_GCMS_Fingerprint.modules.real_data_loader import RealDataLoader, prompt_for_real_data
        print("✓ RealDataLoader imported successfully")
        print("✓ prompt_for_real_data imported successfully")
        
        # Check that run_pipeline can import these
        from HPLC_GCMS_Fingerprint.run_pipeline import parse_args
        print("✓ run_pipeline imports work")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_dataframe_creation():
    """Test creating dummy DataFrames with expected formats."""
    print("\n" + "="*70)
    print("TEST 4: Dummy DataFrame Creation")
    print("="*70)
    
    import pandas as pd
    import numpy as np
    
    # Create HPLC dummy data
    print("\nCreating dummy HPLC data...")
    hplc_data = {
        "sample_id": [f"S{i:03d}" for i in range(10)],
        "species": ["Chlorella_vulgaris"] * 5 + ["Scenedesmus_obliquus"] * 5,
        "phylum": ["Chlorophyta"] * 10,
        "replicate": list(range(1, 6)) + list(range(1, 6)),
    }
    # Add intensity columns
    for i in range(1, 26):
        hplc_data[f"intensity_RT_{i:02d}"] = np.random.uniform(0, 1000, 10)
    # Add activity columns
    hplc_data["activity_ethanol"] = np.random.uniform(0, 100, 10)
    hplc_data["activity_methanol"] = np.random.uniform(0, 100, 10)
    
    hplc_df = pd.DataFrame(hplc_data)
    print(f"✓ Created HPLC DF: {hplc_df.shape}")
    print(f"  Columns: {list(hplc_df.columns[:5])}... ({len(hplc_df.columns)} total)")
    
    # Create GCMS dummy data
    print("\nCreating dummy GCMS data...")
    gcms_data = {
        "sample_id": [f"S{i:03d}" for i in range(10)],
        "species": ["Chlorella_vulgaris"] * 5 + ["Scenedesmus_obliquus"] * 5,
        "phylum": ["Chlorophyta"] * 10,
        "replicate": list(range(1, 6)) + list(range(1, 6)),
    }
    # Add intensity columns
    for i in range(1, 101):
        gcms_data[f"intensity_mz_{i:03d}"] = np.random.uniform(0, 5000, 10)
    # Add activity columns
    gcms_data["activity_ethanol"] = np.random.uniform(0, 100, 10)
    gcms_data["activity_methanol"] = np.random.uniform(0, 100, 10)
    
    gcms_df = pd.DataFrame(gcms_data)
    print(f"✓ Created GCMS DF: {gcms_df.shape}")
    print(f"  Columns: {list(gcms_df.columns[:5])}... ({len(gcms_df.columns)} total)")
    
    # Create FTIR dummy data
    print("\nCreating dummy FTIR data...")
    ftir_data = {
        "sample_id": [f"S{i:03d}" for i in range(10)],
        "species": ["Chlorella_vulgaris"] * 5 + ["Scenedesmus_obliquus"] * 5,
        "phylum": ["Chlorophyta"] * 10,
        "replicate": list(range(1, 6)) + list(range(1, 6)),
    }
    # Add wavenumber columns
    for wn in range(400, 4400, 50):
        ftir_data[f"wn_{wn}"] = np.random.uniform(0, 2, 10)
    # Add activity columns
    ftir_data["activity_ethanol"] = np.random.uniform(0, 100, 10)
    ftir_data["activity_methanol"] = np.random.uniform(0, 100, 10)
    
    ftir_df = pd.DataFrame(ftir_data)
    print(f"✓ Created FTIR DF: {ftir_df.shape}")
    print(f"  Columns: {list(ftir_df.columns[:5])}... ({len(ftir_df.columns)} total)")
    
    return True

def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("  MULTI-SOURCE REAL DATA LOADER – VALIDATION TESTS")
    print("="*70)
    
    tests = [
        test_imports,
        test_fingerprint_specs,
        test_real_data_loader_initialization,
        test_dataframe_creation,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n✗ {test_func.__name__} failed with exception: {e}")
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "="*70)
    print("  VALIDATION SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}  {test_name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("  ✓ All validation tests passed!")
    else:
        print("  ✗ Some tests failed. Review output above.")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
