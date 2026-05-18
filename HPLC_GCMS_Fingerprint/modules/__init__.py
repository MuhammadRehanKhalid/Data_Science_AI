# ============================================================
# HPLC_GCMS_Fingerprint.modules package
# ============================================================
"""
Enhanced modules for multi-source algae species identification.

Modules:
  - taxonomy_fetcher: NCBI taxonomy data fetching
  - data_input_validator: Multi-source data input and validation
  - biodata_collector: Growth conditions and biodata collection
  - prediction_analyzer: Enhanced predictions with confidence
  - report_generator: PDF report generation
  - insights_analyzer: Automated insights from analysis
  - sample_data_generator: Dummy and real data generation/loading
"""

__version__ = "2.0.0"
__author__ = "Research Team"

# "modules" package provides several optional utilities. Importing the whole
# package should not eagerly require heavy optional dependencies (e.g. Biopython).
# Expose only the lightweight `SampleDataGenerator` here to keep imports cheap.
try:
  from .sample_data_generator import SampleDataGenerator
except Exception:
  SampleDataGenerator = None

__all__ = ["SampleDataGenerator"]
