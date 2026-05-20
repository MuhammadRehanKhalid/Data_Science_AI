# Data Mode Guide - Dummy vs Real

## Overview

The enhanced pipeline now supports two data modes:

1. **DUMMY MODE** - Generate realistic synthetic data for testing and demonstrations
2. **REAL MODE** - Load actual data from user-provided CSV or Excel files

## Quick Start

### Using Dummy Mode (Testing/Demo)

```bash
python enhanced_pipeline.py
```

When prompted:
```
Choose data mode:
  [1] DUMMY  - Generate synthetic data for testing
  [2] REAL   - Load actual data from files

Enter choice (1 or 2): 1
```

The pipeline will automatically generate:
- **FTIR data** - Spectroscopy features at different wavenumbers
- **HPLC data** - Pigment concentrations (Chlorophyll, Carotenoids, etc.)
- **GC-MS data** - Metabolite intensities at different m/z ratios

All with realistic species assignments for testing.

### Using Real Mode (Actual Data)

```bash
python enhanced_pipeline.py
```

When prompted:
```
Choose data mode:
  [1] DUMMY  - Generate synthetic data for testing
  [2] REAL   - Load actual data from files

Enter choice (1 or 2): 2
```

You'll be asked to provide file paths for each data source:
```
--- Load FTIR data? (yes/no): yes
File path: C:\Data\ftir_samples.csv

--- Load HPLC data? (yes/no): yes
File path: C:\Data\hplc_samples.csv

--- Load GCMS data? (yes/no): yes
File path: C:\Data\gcms_samples.csv
```

## Data Format Requirements

### FTIR Data Format

**Required columns:**
- `sample_id` - Unique sample identifier (e.g., "FTIR_S001")
- Spectral features at various wavenumbers (at least 5 columns)

**Example CSV:**
```csv
sample_id,wn_1000,wn_1050,wn_1100,wn_1200,wn_1300
FTIR_S001,85.2,82.1,88.5,76.3,79.8
FTIR_S002,81.5,80.2,85.3,74.1,77.5
```

**Optional columns:**
- `species` - True species label (for validation)

### HPLC Data Format

**Required columns:**
- `sample_id` - Unique sample identifier (e.g., "HPLC_S001")
- Pigment concentration columns (at least 3 of):
  - `Chlorophyll_a`
  - `Chlorophyll_b`
  - `Chlorophyll_c`
  - `Xanthophyll`
  - `Lutein`
  - `Beta_carotene`
  - `Fucoxanthin`

**Example CSV:**
```csv
sample_id,Chlorophyll_a,Chlorophyll_b,Xanthophyll
HPLC_S001,125.5,45.2,22.8
HPLC_S002,110.3,38.1,19.5
```

**Optional columns:**
- `species` - True species label
- `retention_time_min` - Retention time

### GC-MS Data Format

**Required columns:**
- `sample_id` - Unique sample identifier (e.g., "GCMS_S001")
- Metabolite intensity columns at different m/z ratios (at least 3 of):
  - `m_z_73` or `m/z_73`
  - `m_z_147` or `m/z_147`
  - `m_z_217` or `m/z_217`
  - `m_z_273` or `m/z_273`
  - `m_z_327` or `m/z_327`
  - `m_z_371` or `m/z_371`

**Example CSV:**
```csv
sample_id,m_z_73,m_z_147,m_z_217
GCMS_S001,1250,1850,2100
GCMS_S002,980,1650,1900
```

**Optional columns:**
- `species` - True species label
- `injection_volume_ul` - Injection volume

## Supported Algae Species

The dummy data generator includes these species:

1. **Chlorella vulgaris** (Green algae - Chlorophyta)
2. **Spirulina platensis** (Cyanobacteria)
3. **Phaeodactylum tricornutum** (Diatom - Bacillariophyta)
4. **Nannochloropsis gaditana** (Eustigmatophyte - Bacillariophyta)
5. **Tetraselmis subcordiformis** (Green algae - Chlorophyta)
6. **Prorocentrum lima** (Dinoflagellate - Dinoflagellata)
7. **Porphyridium purpureum** (Red algae - Rhodophyta)
8. **Ulva intestinalis** (Green algae - Chlorophyta)
9. **Scenedesmus obliquus** (Green algae - Chlorophyta)
10. **Dunaliella tertiolecta** (Green algae - Chlorophyta)

## Pipeline Execution Flow

### Step 0: Data Mode Selection
- Choose between DUMMY or REAL mode
- If DUMMY: Generate synthetic data (specify number of samples)
- If REAL: Load from user-provided files
- Data is saved to `pipeline_output/data/`

### Step 1: Data Source Selection
- Choose which data sources to use (FTIR, HPLC, GC-MS)
- Choose analysis mode (single-source or multi-source)

### Steps 2-6: Complete Analysis
All subsequent steps (biodata collection, predictions, taxonomy analysis, insights, reports) operate on the data loaded in Step 0.

## Features of Dummy Data Generator

### Realistic Synthetic Data
- Species-specific spectral signatures for FTIR
- Species-specific pigment profiles for HPLC
- Species-specific metabolite patterns for GC-MS
- Realistic noise and variation

### Data Validation
The pipeline automatically validates:
- Required columns present
- Minimum number of features
- Data type compatibility
- Sample ID uniqueness

### Example Usage (Python)

```python
from HPLC_GCMS_Fingerprint.modules.sample_data_generator import SampleDataGenerator

# Initialize generator
gen = SampleDataGenerator(random_seed=42)

# Generate dummy data
ftir_df = gen.generate_ftir_data(n_samples=20)
hplc_df = gen.generate_hplc_data(n_samples=20)
gcms_df = gen.generate_gcms_data(n_samples=20)

# Save to CSV
ftir_df.to_csv("ftir_data.csv", index=False)
hplc_df.to_csv("hplc_data.csv", index=False)
gcms_df.to_csv("gcms_data.csv", index=False)

# Load real data
real_data = gen.load_data_from_file("path/to/data.csv")

# Validate data
is_valid, errors = gen.validate_data_structure(real_data, "FTIR")
if is_valid:
    print("Data is valid!")
else:
    print("Validation errors:", errors)

# Print summary
gen.print_data_summary(ftir_df, "FTIR")
```

## Analysis Flow with Sample Data

1. **STEP 0** - Mode selection generates/loads sample data
2. **STEP 1** - User selects which data sources to analyze
3. **STEP 2** - Biodata collection (growth conditions, optional)
4. **STEP 3** - Fetch phylogenetic taxonomy from NCBI (optional)
5. **STEP 4** - **Species predictions on sample data**
   - Analyzes each sample
   - Makes phylogenetic predictions
   - Shows confidence scores
   - Provides top 3 alternatives
6. **STEP 5** - Generate insights from predictions
   - Species distribution
   - Phylum composition
   - Confidence analysis
   - Multi-source agreement
7. **STEP 6** - Generate comprehensive reports
   - PDF reports with predictions
   - Prediction graphs
   - Analysis summaries

## Phylogenetic Analysis

The pipeline performs phylogenetic analysis at Step 4:

### Species-to-Phylum Mapping
Each predicted species is mapped to its phylogenetic phylum:
- **Chlorophyta** - Green algae
- **Bacillariophyta** - Diatoms
- **Cyanobacteria** - Blue-green algae
- **Dinoflagellata** - Dinoflagellates
- **Rhodophyta** - Red algae

### Analysis Output
- Predicted species with confidence scores
- Phylogenetic phylum assignment
- Top 3 alternative species
- Phylum distribution across samples
- Confidence statistics (mean, std, min, max)

## Troubleshooting

### Data Validation Errors

**Error: "Missing required column: sample_id"**
- Ensure your CSV/Excel has a column named exactly `sample_id`

**Error: "FTIR data should have multiple wavenumber columns"**
- FTIR data needs at least 5 spectral feature columns
- Rename columns like `wn_1000`, `wn_1050`, etc.

**Error: "HPLC data should contain pigment concentration columns"**
- Include pigment columns: Chlorophyll_a, Xanthophyll, Beta_carotene, etc.

**Error: "GC-MS data should contain m/z or metabolite intensity columns"**
- Include m/z columns: m_z_73, m_z_147, m_z_217, etc.

### Dummy Data Issues

**All samples predicted as same species:**
- This can happen with small sample sizes
- Generate more samples: enter larger number when prompted
- Check data consistency

### Real Data Issues

**File not found error:**
- Use absolute path: `C:\Users\YourName\Data\samples.csv`
- Ensure file exists before running pipeline

**"Unsupported format" error:**
- Only `.csv`, `.xlsx`, and `.xls` files supported
- Convert other formats to CSV first

## Tips for Best Results

### With Dummy Data
- Use 15-20 samples for testing
- Test both single-source and multi-source modes
- Verify pipeline works before using real data

### With Real Data
- Ensure consistent sample_id format
- Validate data in Excel/CSV before loading
- Start with one data source before multi-source
- Save original data before pipeline processing

### For Accurate Predictions
- Provide data from all three sources (FTIR, HPLC, GC-MS) for best accuracy
- Ensure samples represent actual algae strains
- Include optional `species` column for validation
- Use growth condition metadata (Step 2) for context

## Output Structure

```
pipeline_output/
├── data/
│   ├── ftir_data.csv
│   ├── hplc_data.csv
│   └── gcms_data.csv
├── biodata/
│   ├── biodata.json
│   └── biodata.csv
├── predictions/
│   └── predictions.csv
├── reports/
│   ├── prediction_analysis.pdf
│   ├── insights_report.txt
│   └── graphs/
├── figures/
└── taxonomy/
    └── taxonomy_cache.csv
```

## Next Steps

- [QUICK_START.md](QUICK_START.md) - 5-minute setup guide
- [ENHANCED_PIPELINE_README.md](ENHANCED_PIPELINE_README.md) - Detailed documentation
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Architecture overview
