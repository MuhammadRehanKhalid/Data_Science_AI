# QUICK START GUIDE - Enhanced Algae Pipeline

## 5-Minute Setup

### 1. Install Dependencies
```bash
# Navigate to project directory
cd HPLC_GCMS_Fingerprint

# Install requirements
pip install -r requirements_enhanced.txt

# NCBI requires email (set in taxonomy_fetcher.py)
# Edit: modules/taxonomy_fetcher.py
#   Entrez.email = "your_email@example.com"
```

### 2. Run Pipeline
```bash
python enhanced_pipeline.py
```

### 3. Choose Data Mode
When the pipeline starts, you'll be asked:
```
Choose data mode:
  [1] DUMMY  - Generate synthetic data for testing
  [2] REAL   - Load actual data from files

Enter choice (1 or 2):
```

**DUMMY MODE** (Recommended for first-time users)
- Generates realistic sample data automatically
- Perfect for testing and learning
- No data file preparation needed
- See immediate results

**REAL MODE** (For actual analysis)
- Load your own CSV/Excel data files
- Supports FTIR, HPLC, and GC-MS formats
- Performs actual species identification
- Generates real predictions and reports

### 4. Follow Interactive Prompts
- ✅ Select data sources (FTIR/HPLC/GCMS or combinations)
- ✅ Choose training mode (single or multiple sources)
- ✅ Collect biodata (growth conditions, optional)
- ✅ Fetch taxonomy from NCBI (optional)
- ✅ Get species predictions with phylogenetic analysis
- ✅ Receive automated insights and recommendations
- ✅ Generate PDF reports

---

## What You'll Get

### 📁 Output Folder Structure
```
pipeline_output/
├── data/                    # Sample format guides
├── biodata/                 # Growth conditions (JSON/CSV)
├── predictions/             # Species predictions table
├── taxonomy/               # NCBI taxonomy cache
├── reports/                # PDF and text reports
└── figures/                # Graphs (if generated)
```

### 📄 Key Output Files

| File | Content |
|------|---------|
| `biodata_metadata_*.csv` | Experiment metadata |
| `biodata_samples_*.csv` | Sample growth data |
| `predictions.csv` | Species predictions with confidence |
| `prediction_analysis.pdf` | Professional PDF report |
| `insights_report.txt` | Automated insights and recommendations |
| `taxonomy_cache.csv` | Cached NCBI taxonomy data |

---

## Quick Test: Try Dummy Mode (1 minute)

### Example Session
```bash
$ python enhanced_pipeline.py

# ... Pipeline initializes ...

Choose data mode:
  [1] DUMMY  - Generate synthetic data for testing
  [2] REAL   - Load actual data from files

Enter choice (1 or 2): 1

✓ Dummy mode selected
Sample data will be generated automatically for testing.

How many samples to generate for each data source?
Number of samples (default 10): 10

Generating 10 samples for each source...
✓ Generated FTIR data: 10 samples
✓ Generated HPLC data: 10 samples
✓ Generated GC-MS data: 10 samples

# ... Pipeline continues with automatic analysis ...
# ... Shows species predictions, phyla, confidence scores ...
# ... Generates PDF reports ...
```

### What Happens in Dummy Mode
1. **Synthetic data** is generated for 10 samples (you can choose different number)
2. Each sample gets realistic spectroscopic signatures and true species labels
3. Pipeline performs **full analysis** including:
   - Species predictions
   - Phylogenetic analysis
   - Confidence scoring
   - Multi-source ensemble (if multiple sources selected)
   - Insights generation
   - PDF report generation

---

## Using Real Data: Example CSV Formats

See [DATA_MODES_GUIDE.md](DATA_MODES_GUIDE.md) for detailed format specifications.

### Minimal FTIR Example
```csv
sample_id,wn_1000,wn_1050,wn_1100,wn_1200
S001,85.2,82.1,88.5,76.3
S002,81.5,80.2,85.3,74.1
```

### Minimal HPLC Example
```csv
sample_id,Chlorophyll_a,Xanthophyll,Beta_carotene
S001,125.5,22.8,8.5
S002,110.3,19.5,7.2
```

### Minimal GC-MS Example
```csv
sample_id,m_z_73,m_z_147,m_z_217
S001,1250,1850,2100
S002,980,1650,1900
```

---

## Key Features Explained

### 🎯 Multi-Source Support
- Choose which spectroscopy data to use
- Combine FTIR + HPLC + GC-MS for better accuracy
- Single or ensemble models

### 📊 Biodata Collection
Records growth conditions including:
- Temperature, pH, light conditions
- Culture medium and nutrients
- Cell density and viability
- Extraction methods

### 🔬 NCBI Taxonomy Integration
- Automatic phylum classification
- Complete taxonomic lineage
- Phylum probabilities alongside species

### 📈 Confidence Metrics
Each prediction includes:
- Confidence score (0-100%)
- Entropy (uncertainty measure)
- Top-3 alternative species
- Source agreement (if multi-source)

### 📑 Automated Reports
- Professional PDF with all results
- Growth conditions summary
- Species predictions table
- Recommendations based on confidence
- Insights about your data

---

## Common Workflows

### Workflow 1: Identify Unknown Samples
```
1. Run enhanced_pipeline.py
2. Select "FTIR" (or your instrument)
3. Provide sample data
4. Collect growth conditions
5. Get species predictions + taxonomy
6. Review PDF report with recommendations
```

### Workflow 2: Compare Multiple Data Sources
```
1. Run enhanced_pipeline.py
2. Select "Multiple Source Training" → Choose FTIR, HPLC, GCMS
3. Provide data from all three instruments
4. Get predictions from each source
5. Compare agreement between sources
6. Receive ensemble predictions
7. View insights about source complementarity
```

### Workflow 3: Build Training Dataset
```
1. Run enhanced_pipeline.py
2. Collect biodata for each sample
3. Provide reference spectra
4. Pipeline creates balanced training set
5. Export predictions + biodata for model training
```

---

## Troubleshooting

### Issue: "Missing required columns"
**Solution**: Check CSV headers match format guide in `pipeline_output/data/`

### Issue: "NCBI connection error"
**Solution**: Check internet. Results are cached - rerun to use cache.

### Issue: "Email not set error"
**Solution**: Edit `modules/taxonomy_fetcher.py` and set `Entrez.email`

### Issue: "No PDF generated"
**Solution**: Install reportlab: `pip install reportlab`

### Issue: "ModuleNotFoundError"
**Solution**: Install all requirements: `pip install -r requirements_enhanced.txt`

---

## What Species Are Supported?

Default: 13 algal species across 7 phyla

Add custom species by editing:
`data_generation/constants.py`

```python
# Add to SPECIES list
SPECIES.append("Your species name")

# Add to PHYLA mapping
PHYLA["Your species name"] = "Your phylum"

# Add to baseline (optional)
SPECIES_BASELINE["Your species name"] = 0.70
```

---

## Next Steps

1. **Review output files** in `pipeline_output/`
2. **Read detailed README**: `ENHANCED_PIPELINE_README.md`
3. **Check module docs**: Docstrings in each module file
4. **Customize as needed**: Adapt to your specific use case

---

## Advanced Features

### Use Programmatically
```python
from enhanced_pipeline import EnhancedPipelineOrchestrator
from pathlib import Path

orchestrator = EnhancedPipelineOrchestrator(Path("output"))
orchestrator.step4_make_predictions()
orchestrator.step5_generate_insights()
```

### Custom Configuration
Create `config.json`:
```json
{
  "data_sources": ["FTIR", "HPLC"],
  "species": ["Chlorella vulgaris", "Spirulina platensis"]
}
```
Then run: `python enhanced_pipeline.py --config config.json`

### Batch Processing
```python
from pathlib import Path
from modules.taxonomy_fetcher import NCBITaxonomyFetcher

fetcher = NCBITaxonomyFetcher()
species_list = [...]
df = fetcher.fetch_batch_taxonomy(species_list)
```

---

## Example Output

```
==============================================================
Predicted: Chlorella vulgaris (Chlorophyta)
Confidence: 87.5%
Entropy: 0.92 bits

Top 3 Predictions:
  1. Chlorella vulgaris     (87.5%)
  2. Scenedesmus obliquus   (10.2%)
  3. Ulva intestinalis      (2.3%)

NCBI Taxonomy:
  Kingdom: Eukaryota
  Phylum: Chlorophyta
  Class: Trebouxiophyceae
  Order: Chlorellales
  Family: Chlorellaceae
  Genus: Chlorella
  Species: C. vulgaris
==============================================================
```

---

## Support & Documentation

📖 **Full Documentation**: See `ENHANCED_PIPELINE_README.md`

📚 **Module Documentation**: Review docstrings in each module file

💡 **Examples**: Check `if __name__ == "__main__"` sections in modules

❓ **Questions**: Review module docstrings and examples

---

## Getting Help

1. Check the **Troubleshooting** section above
2. Review module docstrings (detailed explanations)
3. Check the **Advanced Features** section
4. Read ENHANCED_PIPELINE_README.md for complete documentation

---

**You're ready to go!** 🚀

Run: `python enhanced_pipeline.py`
