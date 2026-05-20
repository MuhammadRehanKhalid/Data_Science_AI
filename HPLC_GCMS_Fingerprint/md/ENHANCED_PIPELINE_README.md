# Enhanced Multi-Source Algae Species Identification Pipeline

## Overview

This is an **advanced, production-ready pipeline** for identifying algal species from multi-source spectroscopic data (FTIR, HPLC, GC-MS). It integrates:

- ✅ **Multi-source data input** (FTIR, HPLC, GCMS, single or combined)
- ✅ **NCBI taxonomy fetching** with phylogenetic classification
- ✅ **Biodata collection** for complete reproducibility
- ✅ **Enhanced predictions** with confidence scores and phyla information
- ✅ **PDF report generation** with recommendations
- ✅ **Automated insights** from graphs and predictions
- ✅ **Interactive workflow** guiding users through each step

---

## Installation & Setup

### Prerequisites

```bash
# Core dependencies
pip install pandas numpy scikit-learn

# For NCBI taxonomy fetching
pip install biopython

# For PDF report generation
pip install reportlab

# For deep learning (optional)
pip install torch  # if using DL models

# For visualization
pip install matplotlib seaborn
```

### Configure NCBI Email

Edit `modules/taxonomy_fetcher.py` and set your email:

```python
Entrez.email = "your_email@example.com"  # REQUIRED for NCBI API
```

---

## File Structure

```
HPLC_GCMS_Fingerprint/
├── enhanced_pipeline.py          ← Main orchestrator (START HERE)
├── modules/
│   ├── __init__.py
│   ├── taxonomy_fetcher.py       ← NCBI taxonomy integration
│   ├── data_input_validator.py   ← Multi-source data handling
│   ├── biodata_collector.py      ← Growth conditions collection
│   ├── prediction_analyzer.py    ← Enhanced predictions with taxonomy
│   ├── report_generator.py       ← PDF report generation
│   └── insights_analyzer.py      ← Automated insights from analysis
├── data/                         ← Input data directory
├── pipeline_output/              ← Generated output
│   ├── data/                     ← Sample format files
│   ├── biodata/                  ← Collected biodata (JSON/CSV)
│   ├── predictions/              ← Prediction results
│   ├── reports/                  ← PDF reports and insights
│   ├── figures/                  ← Graphs and visualizations
│   └── taxonomy/                 ← Cached taxonomy data
└── README.md                     ← This file
```

---

## Quick Start

### 1. Run Interactive Pipeline

```bash
cd HPLC_GCMS_Fingerprint
python enhanced_pipeline.py
```

This launches an **interactive workflow** that guides you through:

1. **Data Source Selection** - Choose FTIR, HPLC, GC-MS, or combinations
2. **Format Validation** - Verify your data matches required format
3. **Biodata Collection** - Record growth conditions for reproducibility
4. **Predictions** - Get species identifications with confidence scores
5. **Taxonomy Lookup** - Fetch phylogenetic information from NCBI
6. **Insights Generation** - Automated analysis and recommendations
7. **PDF Reports** - Professional reports with all results

### 2. Data Format Examples

#### FTIR Format (CSV or Excel)
```csv
wavenumber,intensity,sample_id,species
400.5,0.45,S001,Chlorella_vulgaris
401.0,0.48,S001,Chlorella_vulgaris
401.5,0.50,S001,Chlorella_vulgaris
```

#### HPLC Format (CSV or Excel)
```csv
retention_time,peak_area,sample_id,compound_name,wavelength,species
2.34,5632.1,S001,Chlorogenic_acid,254,Chlorella_vulgaris
3.45,8921.3,S001,Rutin,254,Chlorella_vulgaris
5.67,1234.2,S001,Quercetin,280,Chlorella_vulgaris
```

#### GC-MS Format (CSV or Excel)
```csv
retention_time,mz_ratio,intensity,sample_id,compound_name,species
8.23,71.0,2341.5,S001,Toluene,Chlorella_vulgaris
9.45,85.0,5623.2,S001,Xylene,Chlorella_vulgaris
11.34,91.0,892.1,S001,Styrene,Chlorella_vulgaris
```

---

## Module Documentation

### 1. Taxonomy Fetcher (`taxonomy_fetcher.py`)

Fetches real taxonomy data from NCBI for species predictions.

```python
from modules.taxonomy_fetcher import NCBITaxonomyFetcher, PredictionTaxonomyTracer

# Initialize fetcher with caching
fetcher = NCBITaxonomyFetcher(cache_file="taxonomy_cache.csv")

# Fetch single species
result = fetcher.fetch_taxonomy("Chlorella vulgaris")
print(f"Phylum: {result['phylum']}")  # Output: Chlorophyta

# Batch fetch
species_list = ["Chlorella vulgaris", "Spirulina platensis"]
df = fetcher.fetch_batch_taxonomy(species_list)

# Trace predictions back to taxonomy
tracer = PredictionTaxonomyTracer(fetcher)
trace = tracer.trace_prediction(
    predicted_species="Chlorella vulgaris",
    confidence=0.92,
    data_source="FTIR",
    sample_id="S001"
)
```

### 2. Data Input Validator (`data_input_validator.py`)

Guides users through data format selection and validation.

```python
from modules.data_input_validator import DataSourceSelector, MultiSourceDataLoader

# Interactive source selection
selector = DataSourceSelector()
selector.print_welcome()
selected = selector.ask_source_selection()  # Returns ['FTIR', 'HPLC'] etc.

# Load data with validation
loader = MultiSourceDataLoader(selected)
loader.load_all_sources(Path("data"))

# Get unified feature matrix
unified_features = loader.get_unified_features()
```

### 3. Biodata Collector (`biodata_collector.py`)

Captures growth conditions and metadata for reproducibility.

```python
from modules.biodata_collector import BiodataCollector

# Interactive collection
collector = BiodataCollector(output_dir=Path("biodata"))
collector.collect_experiment_metadata()
collector.collect_growth_conditions()
collector.collect_medium_and_nutrients()
collector.collect_environmental_conditions()

# Add samples
collector.add_multiple_samples(n_samples=5)

# Save
collector.save_biodata("json")
collector.save_biodata("csv")
```

### 4. Prediction Analyzer (`prediction_analyzer.py`)

Analyzes predictions with confidence scores and taxonomy.

```python
from modules.prediction_analyzer import PredictionAnalyzer, ConfidenceAssessor
import numpy as np

# Initialize
analyzer = PredictionAnalyzer(species_names, phyla_mapping)

# Analyze single prediction
pred_probs = np.array([0.75, 0.20, 0.05])
analysis = analyzer.analyze_species_prediction(
    pred_class=0,
    pred_probabilities=pred_probs,
    sample_id="S001",
    data_source="FTIR"
)

# Multi-source ensemble
predictions = {
    "FTIR": (0, np.array([0.75, 0.20, 0.05])),
    "HPLC": (0, np.array([0.80, 0.15, 0.05])),
    "GCMS": (1, np.array([0.20, 0.70, 0.10]))
}
ensemble = analyzer.analyze_multi_source_predictions(predictions)

# Assess confidence
assessor = ConfidenceAssessor()
assessment = assessor.assess_confidence(
    confidence=0.75,
    entropy=1.2,
    agreement_pct=85
)
```

### 5. Report Generator (`report_generator.py`)

Creates professional PDF reports.

```python
from modules.report_generator import PDFReportGenerator

# Generate report
gen = PDFReportGenerator(output_dir=Path("reports"))
report_path = gen.generate_prediction_report(
    experiment_metadata=exp_meta,
    biodata=biodata_dict,
    predictions_df=predictions_df,
    predictions_detailed=predictions_list,
    growth_conditions=growth_cond
)

# Generate graph report
gen.generate_graph_report(
    graph_paths=[Path("graph1.png"), Path("graph2.png")],
    graph_descriptions=["Confidence Distribution", "Species Composition"],
    insights=[
        "High confidence predictions (>80%)",
        "Diverse phylum composition"
    ]
)
```

### 6. Insights Analyzer (`insights_analyzer.py`)

Generates automated insights from predictions.

```python
from modules.insights_analyzer import InsightsGenerator, InsightReportBuilder

# Generate insights
gen = InsightsGenerator()
insights = gen.generate_comprehensive_insights(
    predictions_df,
    confidence_scores,
    source_predictions
)

# Create report
builder = InsightReportBuilder()
report = builder.create_insight_report(insights)

# Generate recommendations
recommendations = builder.create_recommendations_from_insights(insights)
```

---

## Key Features

### 🎯 Multi-Source Data Integration

Choose to use:
- **Single source**: FTIR, HPLC, or GC-MS independently
- **Multiple sources**: Combine data for improved accuracy
- **Ensemble predictions**: Merge predictions from different sources

### 📊 Biodata for Reproducibility

Capture detailed information:
- Temperature, pH, light conditions
- Culture medium and nutrients
- Sample collection details
- Cell density and viability
- All saved in structured JSON/CSV format

### 🔬 NCBI Taxonomy Integration

Automatically:
- Fetch scientific names from NCBI
- Get complete taxonomic lineage (Kingdom → Species)
- Cache results for faster future access
- Trace predictions back to phylogenetic information

### 📈 Confidence & Reliability Assessment

Each prediction includes:
- Confidence score (0-1)
- Probability distribution over all species
- Shannon entropy (uncertainty measure)
- Top-3 alternative predictions
- Source agreement metrics (for multi-source)

### 📑 Professional PDF Reports

Generated reports include:
- Experiment metadata and objectives
- Growth conditions summary
- Species prediction table
- Confidence metrics
- Automated recommendations
- Graphs and insights

### 💡 Automated Insights

Pipeline generates insights about:
- Species diversity and distribution
- Phylum composition
- Confidence patterns
- Source agreement
- Replicate consistency
- Actionable recommendations

---

## Supported Algae Species

**Default species in pipeline:**

| Species | Phylum | Notes |
|---------|--------|-------|
| Prorocentrum lima | Dinoflagellata | Dinoflagellate |
| Phaeodactylum tricornutum | Bacillariophyta | Diatom |
| Porphyridium purpureum | Rhodophyta | Red algae |
| Ulva intestinalis | Chlorophyta | Green algae |
| Chlorella vulgaris | Chlorophyta | Green algae |
| Asparagopsis taxiformis | Rhodophyta | Red algae |
| Chromochloris zofingiensis | Chlorophyta | Green algae |
| Spirulina major | Cyanobacteria | Cyanobacteria |
| Alaria esculenta | Phaeophyceae | Brown algae |
| Saccharina latissima | Phaeophyceae | Brown algae |
| Palmaria palmata | Rhodophyta | Red algae |

**To add species**: Edit `data_generation/constants.py`

---

## Output Structure

```
pipeline_output/
├── data/                          # Input data
│   ├── FTIR_FORMAT_README.txt
│   ├── HPLC_FORMAT_README.txt
│   └── GCMS_FORMAT_README.txt
│
├── biodata/                       # Collected biodata
│   ├── biodata_EXP_001_20250514.json
│   ├── biodata_metadata_EXP_001.csv
│   └── biodata_samples_EXP_001.csv
│
├── predictions/                   # Prediction results
│   ├── predictions.csv            # Main predictions table
│   └── prediction_traces.csv      # Species → Taxonomy traces
│
├── taxonomy/                      # NCBI taxonomy cache
│   └── taxonomy_cache.csv
│
├── reports/                       # PDF and text reports
│   ├── prediction_analysis.pdf    # Main PDF report
│   ├── graph_report.pdf           # Graphs and insights
│   └── insights_report.txt        # Text insights
│
└── figures/                       # Visualizations
    ├── 01_confidence_dist.png
    ├── 02_species_composition.png
    └── ...
```

---

## Advanced Usage

### Custom Configuration (Config File Mode)

```json
{
  "output": "custom_output",
  "data_sources": ["FTIR", "HPLC"],
  "training_mode": "multiple",
  "skip_taxonomy": false,
  "skip_reports": false,
  "species": [
    "Chlorella vulgaris",
    "Spirulina platensis"
  ]
}
```

```bash
python enhanced_pipeline.py --config config.json
```

### Programmatic Usage

```python
from enhanced_pipeline import EnhancedPipelineOrchestrator
from pathlib import Path

orchestrator = EnhancedPipelineOrchestrator(
    output_root=Path("my_output")
)

# Execute specific steps
orchestrator.step1_select_and_load_data()
orchestrator.step2_collect_biodata()
orchestrator.step4_make_predictions()
orchestrator.step5_generate_insights()
orchestrator.step6_generate_reports()
```

---

## Troubleshooting

### NCBI Taxonomy Fetching Issues

**Error**: `Entrez.email not set`
- **Solution**: Edit `taxonomy_fetcher.py` and set your email

**Error**: `No internet connection`
- **Solution**: Cached results will be used. Results are saved in `taxonomy/`

**Error**: `ModuleNotFoundError: No module named 'Bio'`
- **Solution**: `pip install biopython`

### PDF Report Generation Issues

**Error**: `ModuleNotFoundError: No module named 'reportlab'`
- **Solution**: `pip install reportlab`

**Note**: Reports will still be generated as text files if reportlab is unavailable

### Data Loading Issues

**Error**: `Missing required columns`
- **Solution**: Check your CSV/Excel format matches the example. See `pipeline_output/data/` for format guides.

---

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{algae_pipeline_2025,
  title={Enhanced Multi-Source Algae Species Identification Pipeline},
  author={Research Team},
  year={2025},
  url={https://github.com/...}
}
```

---

## Contributing

To add new features:

1. Create a new module in `modules/`
2. Add comprehensive docstrings
3. Update `modules/__init__.py`
4. Test with sample data
5. Document in this README

---

## License

See [LICENSE](LICENSE) for the full terms. This project is proprietary and
all rights are reserved unless you have explicit written permission from the
copyright holder.

---

## Support

For issues, questions, or suggestions:

1. Check the **Troubleshooting** section above
2. Review module docstrings
3. Check example usage in each module's `__main__` section
4. Review generated output files for diagnostics

---

## Changelog

### Version 2.0.0 (Current)
- ✅ Multi-source data support (FTIR, HPLC, GC-MS)
- ✅ NCBI taxonomy integration
- ✅ Biodata collection system
- ✅ Enhanced predictions with confidence
- ✅ PDF report generation
- ✅ Automated insights analyzer
- ✅ Interactive orchestrator pipeline

### Version 1.0.0
- Initial HPLC/GC-MS pipeline

---

**Last Updated**: May 14, 2025

**Maintained By**: Research Team

**Status**: Production Ready ✅
