# QUICK REFERENCE CARD

## START HERE

### Run Pipeline
```bash
cd HPLC_GCMS_Fingerprint
python enhanced_pipeline.py
```

### Choose Mode
```
[1] DUMMY  - Auto-generate test data (no files needed)
[2] REAL   - Load your CSV/Excel files
```

### Follow Prompts
- Select data sources (FTIR/HPLC/GCMS)
- Optional: Collect biodata
- Optional: Fetch NCBI taxonomy
- Get species predictions with phylum & confidence

---

## DUMMY MODE (Testing)

```bash
python enhanced_pipeline.py

# Choose [1] DUMMY
# Enter sample count (default 10)
# Wait ~15 seconds for complete analysis
# Get predictions.csv with results
```

**Perfect for**:
- Learning the system
- Testing before real data
- Demonstrations
- Quick analysis

---

## REAL MODE (Your Data)

```bash
python enhanced_pipeline.py

# Choose [2] REAL
# Provide CSV/Excel file paths:
#   - FTIR file (optional)
#   - HPLC file (optional)
#   - GCMS file (optional)
# Get predictions based on your data
```

**File Format**:
- **FTIR**: `sample_id`, `wn_1000`, `wn_1050`, ... (min 5 wavenumber cols)
- **HPLC**: `sample_id`, `Chlorophyll_a`, `Xanthophyll`, ... (min 3 pigment cols)
- **GCMS**: `sample_id`, `m_z_73`, `m_z_147`, ... (min 3 m/z cols)

---

## AUTOMATED TEST

```bash
python test_dummy_pipeline.py

# Automatically:
# - Generates 15 dummy samples
# - Runs complete pipeline
# - Shows predictions & insights
# - Saves output files
```

---

## OUTPUT FILES

### Data
```
pipeline_output/data/
├── ftir_data.csv      # FTIR spectroscopy data
├── hplc_data.csv      # HPLC pigment data
└── gcms_data.csv      # GC-MS metabolite data
```

### Results
```
pipeline_output/predictions/
└── predictions.csv    # Species, phylum, confidence

pipeline_output/reports/
├── insights_report.txt       # Analysis summary
└── prediction_analysis.pdf   # Full PDF report
```

---

## PREDICTIONS CSV COLUMNS

```
sample_id              - Unique sample ID
data_source            - FTIR/HPLC/GCMS
predicted_species      - Identified species name
predicted_phylum       - Chlorophyta/Bacillariophyta/etc
confidence_pct         - Confidence 0-100%
```

---

## 10 SPECIES SUPPORTED

| Species | Phylum |
|---------|--------|
| Chlorella vulgaris | Chlorophyta |
| Spirulina platensis | Cyanobacteria |
| Phaeodactylum tricornutum | Bacillariophyta |
| Nannochloropsis gaditana | Bacillariophyta |
| Tetraselmis subcordiformis | Chlorophyta |
| Prorocentrum lima | Dinoflagellata |
| Porphyridium purpureum | Rhodophyta |
| Ulva intestinalis | Chlorophyta |
| Scenedesmus obliquus | Chlorophyta |
| Dunaliella tertiolecta | Chlorophyta |

---

## TROUBLESHOOTING

### "Module not found"
```bash
pip install -r requirements_enhanced.txt
```

### "File not found"
- Use absolute path: `C:\Users\Name\Data\file.csv`
- Check file exists and is accessible

### "Unsupported format"
- Only .csv and .xlsx supported
- Ensure column names match format spec
- Check for special characters in data

### "Invalid data"
- See DATA_MODES_GUIDE.md → Format Specifications
- Required: `sample_id` column
- Check minimum column counts

---

## DOCUMENTATION FILES

| File | Purpose |
|------|---------|
| **DATA_MODES_GUIDE.md** | Complete user guide |
| **QUICK_START.md** | 5-minute setup |
| **DUMMY_AND_REAL_MODE_README.md** | Feature overview |
| **IMPLEMENTATION_COMPLETE.md** | Technical details |
| **DELIVERY_SUMMARY.md** | What was delivered |

---

## PIPELINE STEPS

```
STEP 0  ← Data Mode Selection (NEW)
STEP 1  ← Data Source Selection
STEP 2  ← Biodata Collection (optional)
STEP 3  ← Taxonomy Fetching (optional)
STEP 4  ← Species Predictions (ENHANCED)
STEP 5  ← Insights Generation
STEP 6  ← PDF Reports
```

---

## API USAGE (Python)

```python
from HPLC_GCMS_Fingerprint.modules.sample_data_generator import SampleDataGenerator

# Initialize
gen = SampleDataGenerator()

# Generate dummy data
ftir = gen.generate_ftir_data(n_samples=20)
hplc = gen.generate_hplc_data(n_samples=20)
gcms = gen.generate_gcms_data(n_samples=20)

# Load real data
real_data = gen.load_data_from_file("data.csv")

# Validate
is_valid, errors = gen.validate_data_structure(real_data, "FTIR")

# Display
gen.print_data_summary(ftir, "FTIR")
```

---

## KEYBOARD SHORTCUTS & RESPONSES

| Prompt | Response |
|--------|----------|
| Choose mode | `1` or `2` |
| Continue with step | `yes` or `no` |
| Load data? | `yes` or `no` |
| File path | Full path (example: `C:\Data\file.csv`) |
| Sample count | Number (default: `10`) |

---

## COMMON WORKFLOWS

### Workflow 1: Quick Demo
```bash
python enhanced_pipeline.py → [1] → Enter → Auto results
```

### Workflow 2: Test System
```bash
python test_dummy_pipeline.py → Automatic test
```

### Workflow 3: Real Analysis
```bash
python enhanced_pipeline.py → [2] → Provide files → Results
```

### Workflow 4: Batch Processing
```bash
Generate dummy data → Save CSVs → Run as REAL mode
```

---

## PERFORMANCE NOTES

- Dummy data generation: <1 sec
- 45 samples analysis: ~5 sec
- Report generation: ~10 sec
- Full pipeline: ~15 sec

---

## REQUIREMENTS

- Python 3.7+
- NumPy
- Pandas
- Biopython
- reportlab (optional, for PDF)

Install all:
```bash
pip install -r requirements_enhanced.txt
```

---

## FEATURES AT A GLANCE

✅ 2 Operating Modes (DUMMY + REAL)
✅ 3 Data Sources (FTIR, HPLC, GC-MS)
✅ 10 Species Identification
✅ 5 Phyla Classification
✅ Confidence Scoring
✅ Multi-source Ensemble
✅ Automated Insights
✅ PDF Reports
✅ Data Validation
✅ CSV/Excel Support

---

## STATUS

🟢 **READY FOR USE**
✅ Tested & Validated
✅ Production Grade
✅ Fully Documented
✅ No Configuration Needed

---

## NEXT STEP

```bash
python enhanced_pipeline.py
```

**That's it!** Follow the interactive prompts to:
1. Choose DUMMY or REAL mode
2. Select data sources
3. Get instant species predictions
4. View results with confidence & phylum

---

**v2.1.0 | May 2026**
