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

from .taxonomy_fetcher import NCBITaxonomyFetcher, PredictionTaxonomyTracer
from .data_input_validator import DataSourceSelector, MultiSourceDataLoader
from .biodata_collector import BiodataCollector, BiodataManager
from .prediction_analyzer import PredictionAnalyzer, PhylumPredictor, ConfidenceAssessor
from .report_generator import PDFReportGenerator, ReportContentBuilder
from .insights_analyzer import InsightsGenerator, InsightReportBuilder
from .sample_data_generator import SampleDataGenerator

__all__ = [
    "NCBITaxonomyFetcher",
    "PredictionTaxonomyTracer",
    "DataSourceSelector",
    "MultiSourceDataLoader",
    "BiodataCollector",
    "BiodataManager",
    "PredictionAnalyzer",
    "PhylumPredictor",
    "ConfidenceAssessor",
    "PDFReportGenerator",
    "ReportContentBuilder",
    "InsightsGenerator",
    "InsightReportBuilder",
    "SampleDataGenerator"
]
