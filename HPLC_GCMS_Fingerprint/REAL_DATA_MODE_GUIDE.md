# Multi-Source Real Data Mode – Complete Implementation

## Overview

The HPLC/GC-MS/FTIR multi-task pipeline has been fully wired to support **real data mode** for all source combinations. Previously, the pipeline would fall back to dummy data generation even when users selected real data mode. Now you can:

✓ Load real **FTIR** data  
✓ Load real **HPLC** data  
✓ Load real **GCMS** (GC-MS) data  
✓ Mix and match any combination of the above  

## Key Changes

### 1. New Real Data Loader Module
**File:** `HPLC_GCMS_Fingerprint/modules/real_data_loader.py`

Provides:
- `RealDataLoader` class for loading fingerprint data from CSV/Excel files
- `prompt_for_real_data()` function for interactive file selection
- Support for all source types (FTIR, HPLC, GCMS)
- Automatic validation and alignment of samples across sources

### 2. Updated Pipeline
**File:** `HPLC_GCMS_Fingerprint/run_pipeline.py`

Changes:
- Removed hardcoded fallback to dummy mode
- Integrated real data loader with source selection
- Added flexible data handling for any source combination
- Supports both dummy and real data modes seamlessly

### 3. Data Format Specifications

Each data source expects a specific column format:

#### FTIR Data
```
Required columns:
  • sample_id        : Unique sample identifier
  • species          : Species name
  • phylum           : Phylum classification
  • replicate        : Replicate number
  • wn_*             : Wavenumber columns (e.g., wn_400.5, wn_401.0)
  • activity_*       : Activity columns per solvent (optional but recommended)
  • <assay>_*        : Assay columns per solvent (optional)

Example column names:
  wn_400.5, wn_401.0, wn_401.5, ..., activity_ethanol, activity_methanol
```

#### HPLC Data
```
Required columns:
  • sample_id        : Unique sample identifier
  • species          : Species name
  • phylum           : Phylum classification
  • replicate        : Replicate number
  • intensity_RT_*   : Binned retention time columns (e.g., intensity_RT_01, intensity_RT_02)
  • activity_*       : Activity columns per solvent (optional but recommended)
  • <assay>_*        : Assay columns per solvent (optional)

Example column names:
  intensity_RT_01, intensity_RT_02, ..., intensity_RT_25, activity_ethanol
```

#### GCMS Data
```
Required columns:
  • sample_id        : Unique sample identifier
  • species          : Species name
  • phylum           : Phylum classification
  • replicate        : Replicate number
  • intensity_mz_*   : Binned m/z columns (e.g., intensity_mz_001, intensity_mz_002)
  • activity_*       : Activity columns per solvent (optional but recommended)
  • <assay>_*        : Assay columns per solvent (optional)

Example column names:
  intensity_mz_001, intensity_mz_002, ..., intensity_mz_100, activity_ethanol
```

## Usage

### Basic Usage with Real Data

```bash
python run_pipeline.py
```

Interactive prompts:
1. Select data mode: Choose `real` (not `dummy`)
2. Select sources: Choose FTIR, HPLC, GCMS (or any combination)
3. Provide file paths: When prompted for each source
4. Add metadata: Optional biodata collection

### Example Session

```
[Step 0 – Data Mode Selection]
Select data mode (dummy/real): real

[OK] Selected data mode: REAL
[OK] Using REAL data mode for analysis

[Source Selection]
Available Data Sources:
  1. FTIR (Fourier-Transform Infrared Spectroscopy)
  2. HPLC (High-Performance Liquid Chromatography)
  3. GCMS (Gas Chromatography - Mass Spectrometry)

Enter the numbers of sources you want to use (comma-separated): 1,2,3
✓ Selected: FTIR, HPLC, GCMS

[Real Data Loader – Multi-Source Fingerprint Data]

FTIR (Fourier-Transform Infrared Spectroscopy)
  Features: Spectral wavenumber columns (wn_*) + metadata
  Files: CSV (.csv) or Excel (.xlsx)

HPLC (High-Performance Liquid Chromatography)
  Features: Binned retention time columns (intensity_RT_*) + metadata
  Files: CSV (.csv) or Excel (.xlsx)

GCMS (Gas Chromatography - Mass Spectrometry)
  Features: Binned m/z ratio columns (intensity_mz_*) + metadata
  Files: CSV (.csv) or Excel (.xlsx)

[LOAD DATA FOR SELECTED SOURCES]

Searching in: /path/to/data/

FTIR:
  Available files:
    1. ftir_data.csv
    2. ftir_analysis.xlsx
  Enter file name (or number 1-2): 1
  ✓ Loaded 45 samples with 80 features

HPLC:
  Available files:
    1. hplc_data.csv
  Enter file name (or number 1-1): 1
  ✓ Loaded 45 samples with 25 features

GCMS:
  Available files:
    1. gcms_data.csv
  Enter file name (or number 1-1): 1
  ✓ Loaded 45 samples with 100 features

Loaded 3 source(s): FTIR, HPLC, GCMS
Align samples across sources? (y/n, default: y): y

[OK] Data loaded successfully
```

## Advanced Usage

### Load Specific Sources Only

The pipeline automatically handles any combination:

```bash
# FTIR only
# Select: 1

# HPLC + GCMS (traditional combination)
# Select: 2,3

# FTIR + HPLC (for spectral + chromatography fusion)
# Select: 1,2
```

### Programmatic Usage

```python
from HPLC_GCMS_Fingerprint.modules.real_data_loader import RealDataLoader
import pandas as pd

# Initialize loader for multiple sources
loader = RealDataLoader(["FTIR", "HPLC", "GCMS"])

# Load from directory
data = loader.load_from_directory("./my_data/")

# Or load with specific file paths
data = loader.load_from_files({
    "FTIR": "data/ftir.csv",
    "HPLC": "data/hplc.csv",
    "GCMS": "data/gcms.csv"
})

# Access loaded data
ftir_df = data.get("FTIR")  # Returns DataFrame or None
hplc_df = data.get("HPLC")
gcms_df = data.get("GCMS")

# Use with dataset builder
from HPLC_GCMS_Fingerprint.ingestion import MultiTaskDataset

dataset = MultiTaskDataset.from_sources(
    hplc_df=hplc_df,
    gcms_df=gcms_df,
    ftir_df=ftir_df
)
```

## Data Preparation Guide

### Step 1: Prepare Your Data

Organize your experimental data into CSV or Excel files with the required format.

**For FTIR:**
- Export wavenumber × absorbance matrix
- Add metadata columns: sample_id, species, phylum, replicate
- Add activity measurements if available

**For HPLC:**
- Create binned retention time features (RT_01, RT_02, ..., RT_25)
- Peak areas or heights for each bin per sample
- Add metadata columns
- Add activity measurements

**For GCMS:**
- Create binned m/z features (mz_001, mz_002, ..., mz_100)
- Peak areas/heights for each m/z bin per sample
- Add metadata columns
- Add activity measurements

### Step 2: Example CSV Structure

**FTIR example (first 5 columns):**
```
sample_id,species,phylum,replicate,wn_400.5,wn_401.0,...
S001,Chlorella_vulgaris,Chlorophyta,1,0.45,0.48,...
S002,Chlorella_vulgaris,Chlorophyta,2,0.42,0.51,...
...
```

**HPLC example (first 5 columns):**
```
sample_id,species,phylum,replicate,intensity_RT_01,intensity_RT_02,...
S001,Chlorella_vulgaris,Chlorophyta,1,1234.5,5678.9,...
S002,Chlorella_vulgaris,Chlorophyta,2,1345.2,5234.1,...
...
```

**GCMS example (first 5 columns):**
```
sample_id,species,phylum,replicate,intensity_mz_001,intensity_mz_002,...
S001,Chlorella_vulgaris,Chlorophyta,1,2341.5,1892.3,...
S002,Chlorella_vulgaris,Chlorophyta,2,2156.8,2034.5,...
...
```

### Step 3: Prepare Activity/Assay Columns (Optional)

For training predictive models, add columns for:
- `activity_<solvent>`: e.g., activity_ethanol, activity_methanol
- `<assay>_<solvent>`: e.g., dpph_ethanol, frap_methanol

```
activity_ethanol,activity_methanol,dpph_ethanol,frap_methanol,...
45.2,52.3,48.1,51.9,...
```

## File Organization

Recommended directory structure for your data:

```
my_analysis/
├── ftir_data.csv
├── hplc_data.csv
├── gcms_data.csv
└── metadata.xlsx
```

Or by type:
```
my_analysis/
├── spectroscopy/
│   └── ftir_data.csv
├── chromatography/
│   ├── hplc_data.csv
│   └── gcms_data.csv
└── metadata.xlsx
```

## Troubleshooting

### "No feature columns found with pattern..."

**Problem:** The loader can't find the expected columns.
**Solution:** Check column naming:
- FTIR: columns should start with `wn_` (e.g., `wn_400.5`)
- HPLC: columns should start with `intensity_RT_` (e.g., `intensity_RT_01`)
- GCMS: columns should start with `intensity_mz_` (e.g., `intensity_mz_001`)

### "Missing required columns: ..."

**Problem:** Missing metadata columns.
**Solution:** Ensure your CSV has these columns:
- `sample_id`
- `species`
- `phylum`
- `replicate`

### "No common sample_ids found across sources"

**Problem:** Sample IDs don't match between sources.
**Solution:** 
- Use consistent sample IDs across all files
- The loader will filter to common samples if you align (recommended)

### Files aren't found in directory

**Problem:** The loader doesn't see your files.
**Solution:**
- Use absolute paths: `/full/path/to/data/` (not relative)
- Check file extensions (.csv or .xlsx, not .xls)
- Ensure files are in the directory specified

## Testing

Run the validation test suite:

```bash
python HPLC_GCMS_Fingerprint/test_real_data_loader.py
```

This verifies:
- ✓ RealDataLoader can handle all source combinations
- ✓ Fingerprint specifications are correctly defined
- ✓ Integration with run_pipeline is functional
- ✓ DataFrame creation works correctly

## Performance Notes

- Single source (FTIR only): ~15-30 seconds for full pipeline
- Dual sources (HPLC + GCMS): ~20-45 seconds
- Triple sources (FTIR + HPLC + GCMS): ~30-60 seconds

(Times depend on dataset size and model training epochs)

## Next Steps

1. **Prepare Your Data** – Convert your experimental data to the required CSV format
2. **Run Pipeline** – Start with `python run_pipeline.py` and select real mode
3. **Explore Results** – Check the generated figures and reports
4. **Optimize** – Use hyperparameter tuning for your specific dataset

## API Reference

### RealDataLoader Class

```python
class RealDataLoader:
    def __init__(self, selected_sources: List[str])
    def print_welcome(self) -> None
    def load_from_directory(self, data_dir: Path | str) -> Dict[str, pd.DataFrame]
    def load_from_files(self, file_mapping: Dict[str, Path | str]) -> Dict[str, pd.DataFrame]
    def align_samples(self) -> Dict[str, pd.DataFrame]
    def get_loaded_data(self) -> Dict[str, Optional[pd.DataFrame]]
```

### Helper Function

```python
def prompt_for_real_data(
    selected_sources: List[str],
    default_data_dir: Optional[Path | str] = None
) -> Dict[str, Optional[pd.DataFrame]]:
    """
    Interactively prompt user to load real data for selected sources.
    """
```

## Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Run the validation test: `python test_real_data_loader.py`
3. Review your data format against the examples
4. Check the console output for detailed error messages
