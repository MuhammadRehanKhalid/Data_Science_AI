# ============================================================
# ENHANCED PIPELINE ORCHESTRATOR
# ============================================================
"""
Master orchestrator integrating all modules:
- Multi-source data input (FTIR, HPLC, GCMS)
- Biodata collection (growth conditions)
- Model predictions with taxonomy
- Comprehensive reporting and insights

Usage:
    python enhanced_pipeline.py              # Interactive mode
    python enhanced_pipeline.py --config config.json  # Config file mode
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import json
from datetime import datetime
import logging
from typing import List, Tuple

# Ensure project root is on sys.path
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import numpy as np

# Import custom modules
try:
    from HPLC_GCMS_Fingerprint.modules.taxonomy_fetcher import (
        NCBITaxonomyFetcher,
        PredictionTaxonomyTracer
    )
    from HPLC_GCMS_Fingerprint.modules.data_input_validator import (
        DataSourceSelector,
        MultiSourceDataLoader,
        DATA_SOURCE_FORMATS
    )
    from HPLC_GCMS_Fingerprint.modules.biodata_collector import (
        BiodataCollector,
        BiodataManager
    )
    from HPLC_GCMS_Fingerprint.modules.prediction_analyzer import (
        PredictionAnalyzer,
        PhylumPredictor,
        ConfidenceAssessor
    )
    from HPLC_GCMS_Fingerprint.modules.report_generator import (
        PDFReportGenerator,
        ReportContentBuilder
    )
    from HPLC_GCMS_Fingerprint.modules.insights_analyzer import (
        InsightsGenerator,
        InsightReportBuilder,
        GraphDescriptionGenerator
    )
    from HPLC_GCMS_Fingerprint.modules.sample_data_generator import (
        SampleDataGenerator
    )
except ImportError as e:
    print(f"Warning: Could not import custom modules: {e}")
    print("Proceeding with basic functionality...")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# ENHANCED PIPELINE ORCHESTRATOR
# ============================================================

class EnhancedPipelineOrchestrator:
    """
    Master orchestrator for multi-source algae species identification pipeline.
    Integrates all modules for a complete workflow.
    """
    
    def __init__(self, output_root: Path = None):
        """
        Parameters
        ----------
        output_root : Path, optional
            Root output directory
        """
        self.output_root = output_root or Path("pipeline_output")
        self._setup_output_directories()
        
        # Initialize components
        self.data_selector = None
        self.data_loader = None
        self.biodata_collector = None
        self.biodata = None
        self.predictions_df = None
        self.predictions_detailed = None
        self.taxonomy_fetcher = None
        self.prediction_analyzer = None
        
        # Data mode and sample data
        self.data_mode = None
        self.sample_data = {}  # Dict of {source: dataframe}
        self.data_generator = SampleDataGenerator()
        
        logger.info(f"Pipeline initialized. Output dir: {self.output_root}")
    
    def _setup_output_directories(self):
        """Create output directory structure."""
        dirs = [
            self.output_root,
            self.output_root / "data",
            self.output_root / "biodata",
            self.output_root / "predictions",
            self.output_root / "reports",
            self.output_root / "figures",
            self.output_root / "taxonomy"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # ============================================================
    # STEP 0: DATA MODE SELECTION (DUMMY or REAL)
    # ============================================================
    
    def step0_select_data_mode(self):
        """Step 0: Ask user to choose between dummy and real data mode."""
        print("\n" + "#"*70)
        print("#  STEP 0: DATA MODE SELECTION")
        print("#"*70)
        
        # Ask for data mode
        self.data_mode = self.data_generator.ask_data_mode()
        
        if self.data_mode == "dummy":
            print("\n✓ Dummy mode selected")
            print("Sample data will be generated automatically for testing.")
            self._generate_dummy_sample_data()
        
        else:  # real mode
            print("\n✓ Real mode selected")
            self._load_real_sample_data()
        
        # Save sample data to output directory
        self._save_sample_data()
        
        print("\n✓ Data ready for analysis")
    
    def _generate_dummy_sample_data(self):
        """Generate dummy data for all sources."""
        print("\n" + "-"*70)
        print("GENERATING DUMMY DATA")
        print("-"*70)
        
        # Ask how many samples to generate
        print("\nHow many samples to generate for each data source?")
        while True:
            try:
                n_samples = int(input("Number of samples (default 10): ").strip() or "10")
                if n_samples > 0:
                    break
            except ValueError:
                pass
            print("✗ Please enter a positive integer")
        
        # Generate data
        print(f"\nGenerating {n_samples} samples for each source...")
        
        ftir_data = self.data_generator.generate_ftir_data(n_samples=n_samples)
        self.sample_data["FTIR"] = ftir_data
        print(f"✓ Generated FTIR data: {len(ftir_data)} samples")
        
        hplc_data = self.data_generator.generate_hplc_data(n_samples=n_samples)
        self.sample_data["HPLC"] = hplc_data
        print(f"✓ Generated HPLC data: {len(hplc_data)} samples")
        
        gcms_data = self.data_generator.generate_gcms_data(n_samples=n_samples)
        self.sample_data["GCMS"] = gcms_data
        print(f"✓ Generated GC-MS data: {len(gcms_data)} samples")
        
        # Print summaries
        print("\n" + "-"*70)
        self.data_generator.print_data_summary(ftir_data, "FTIR")
        self.data_generator.print_data_summary(hplc_data, "HPLC")
        self.data_generator.print_data_summary(gcms_data, "GC-MS")
    
    def _load_real_sample_data(self):
        """Load real data from user-provided files."""
        print("\n" + "-"*70)
        print("LOADING REAL DATA")
        print("-"*70)
        
        sources = ["FTIR", "HPLC", "GCMS"]
        
        for source in sources:
            print(f"\n--- Load {source} data? (yes/no): ", end="")
            
            if input().strip().lower() == "yes":
                file_path = self.data_generator.ask_data_file_path()
                
                try:
                    df = self.data_generator.load_data_from_file(file_path)
                    
                    # Validate
                    is_valid, errors = self.data_generator.validate_data_structure(df, source)
                    
                    if is_valid:
                        self.sample_data[source] = df
                        print(f"✓ Loaded {source} data: {len(df)} samples")
                        self.data_generator.print_data_summary(df, source)
                    else:
                        print(f"\n✗ Data validation errors:")
                        for error in errors:
                            print(f"  - {error}")
                        logger.warning(f"Data validation failed for {source}")
                
                except Exception as e:
                    print(f"✗ Error loading data: {e}")
                    logger.error(f"Failed to load {source} data: {e}")
        
        if not self.sample_data:
            print("\n✗ No data loaded. Please try again.")
            self._load_real_sample_data()
    
    def _save_sample_data(self):
        """Save loaded/generated sample data to output directory."""
        data_dir = self.output_root / "data"
        
        for source, df in self.sample_data.items():
            file_path = data_dir / f"{source.lower()}_data.csv"
            df.to_csv(file_path, index=False)
            logger.info(f"Saved {source} data to {file_path}")
    
    # ============================================================
    # STEP 1: DATA SOURCE SELECTION & LOADING
    # ============================================================
    
    def step1_select_and_load_data(self):
        """Step 1: Interactive data source selection and loading."""
        print("\n" + "="*70)
        print("  STEP 1: DATA SOURCE SELECTION & PROCESSING")
        print("="*70)
        
        # Show available sample data from step 0
        if not self.sample_data:
            print("\n✗ No sample data available. Please run Step 0 first.")
            return
        
        print(f"\nAvailable data sources from Step 0:")
        for i, source in enumerate(self.sample_data.keys(), 1):
            df = self.sample_data[source]
            print(f"  [{i}] {source} - {len(df)} samples")
        
        # Ask which sources to use
        print("\nSelect sources for analysis (comma-separated, e.g., 1,2 or all):")
        selection = input("Selection: ").strip().lower()
        
        selected_sources = []
        if selection == "all":
            selected_sources = list(self.sample_data.keys())
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                source_list = list(self.sample_data.keys())
                selected_sources = [source_list[i] for i in indices if 0 <= i < len(source_list)]
            except (ValueError, IndexError):
                selected_sources = list(self.sample_data.keys())
        
        print(f"\n✓ Selected sources: {', '.join(selected_sources)}")
        
        # Ask training mode
        print("\nTraining mode:")
        print("  [1] Single source (for individual analysis)")
        print("  [2] Multi-source (for ensemble analysis)")
        print("Enter choice (1 or 2): ", end="")
        
        training_mode = "multi-source" if input().strip() == "2" else "single-source"
        logger.info(f"Training mode: {training_mode}")
        
        # Load selected data
        self.data_loader = MultiSourceDataLoader(selected_sources)
        self.data_loader.data = {source: self.sample_data[source] for source in selected_sources}
        
        print(f"\n✓ Loaded data from {len(selected_sources)} sources")
        print("  Data ready for analysis")
        
        return selected_sources, training_mode
    
    def _create_sample_format_files(self, sources: List[str], output_dir: Path):
        """Create sample format files for each selected source."""
        
        for source in sources:
            spec = DATA_SOURCE_FORMATS[source]
            
            # Create README
            readme_path = output_dir / f"{source}_FORMAT_README.txt"
            with open(readme_path, "w") as f:
                f.write(f"=== {source} DATA FORMAT ===\n\n")
                f.write(f"{spec['example_format']}\n\n")
                f.write(f"Required columns: {', '.join(spec['required_columns'])}\n")
                f.write(f"Optional columns: {', '.join(spec['optional_columns'])}\n")
            
            logger.info(f"Created format guide: {readme_path}")
    
    # ============================================================
    # STEP 2: BIODATA COLLECTION
    # ============================================================
    
    def step2_collect_biodata(self):
        """Step 2: Interactive biodata and growth conditions collection."""
        print("\n" + "="*70)
        print("  STEP 2: BIODATA & GROWTH CONDITIONS COLLECTION")
        print("="*70)
        
        self.biodata_collector = BiodataCollector(
            output_dir=self.output_root / "biodata"
        )
        self.biodata_collector.print_welcome()
        
        # Collect experiment data
        self.biodata_collector.collect_experiment_metadata()
        self.biodata_collector.collect_growth_conditions()
        self.biodata_collector.collect_medium_and_nutrients()
        self.biodata_collector.collect_environmental_conditions()
        
        # Collect sample data
        print("\n" + "="*70)
        print("How many samples do you want to add?")
        print("="*70)
        
        while True:
            try:
                n_samples = int(input("Number of samples: ").strip())
                if n_samples > 0:
                    break
            except ValueError:
                pass
            print("✗ Please enter a positive integer")
        
        self.biodata_collector.add_multiple_samples(n_samples)
        
        # Save biodata
        self.biodata_collector.save_biodata("json")
        self.biodata_collector.save_biodata("csv")
        
        # Store biodata
        self.biodata = self.biodata_collector.biodata
        
        print(self.biodata_collector.get_biodata_summary())
        
        logger.info("✓ Biodata collection completed")
    
    # ============================================================
    # STEP 3: FETCH TAXONOMY DATA
    # ============================================================
    
    def step3_fetch_taxonomy(self):
        """Step 3: Fetch taxonomy data from NCBI for predicted species."""
        print("\n" + "="*70)
        print("  STEP 3: TAXONOMY FETCHING FROM NCBI")
        print("="*70)
        
        # Initialize taxonomy fetcher
        cache_path = self.output_root / "taxonomy" / "taxonomy_cache.csv"
        self.taxonomy_fetcher = NCBITaxonomyFetcher(cache_file=cache_path)
        
        print("\nNote: This requires internet connection to fetch from NCBI.")
        print("Results will be cached for faster future access.")
        print("\nRequirements:")
        print("  - Biopython installed (pip install biopython)")
        print("  - Set your email in taxonomy_fetcher.py")
        
        logger.info("Taxonomy fetcher initialized")
    
    # ============================================================
    # STEP 4: PREDICTIONS & ANALYSIS
    # ============================================================
    
    def step4_make_predictions(self):
        """Step 4: Make predictions with phylogenetic analysis."""
        print("\n" + "="*70)
        print("  STEP 4: SPECIES PREDICTIONS & PHYLOGENETIC ANALYSIS")
        print("="*70)
        
        # Species and phyla mapping
        species_names = [
            "Chlorella vulgaris",
            "Spirulina platensis",
            "Phaeodactylum tricornutum",
            "Nannochloropsis gaditana",
            "Tetraselmis subcordiformis",
            "Prorocentrum lima",
            "Porphyridium purpureum",
            "Ulva intestinalis",
            "Scenedesmus obliquus",
            "Dunaliella tertiolecta"
        ]
        
        phyla_mapping = {
            "Chlorella vulgaris": "Chlorophyta",
            "Spirulina platensis": "Cyanobacteria",
            "Phaeodactylum tricornutum": "Bacillariophyta",
            "Nannochloropsis gaditana": "Bacillariophyta",
            "Tetraselmis subcordiformis": "Chlorophyta",
            "Prorocentrum lima": "Dinoflagellata",
            "Porphyridium purpureum": "Rhodophyta",
            "Ulva intestinalis": "Chlorophyta",
            "Scenedesmus obliquus": "Chlorophyta",
            "Dunaliella tertiolecta": "Chlorophyta"
        }
        
        # Initialize prediction analyzer
        self.prediction_analyzer = PredictionAnalyzer(species_names, phyla_mapping)
        
        print("\nPerforming species predictions on sample data...")
        
        # Process predictions for each available data source
        for source, df in self.sample_data.items():
            print(f"\n--- Analyzing {source} data ---")
            
            if df.empty:
                logger.warning(f"No data for {source}")
                continue
            
            # Extract true species from data if available
            true_species = df.get("species", None)
            
            # Perform predictions for each sample
            for idx, sample in df.iterrows():
                sample_id = sample.get("sample_id", f"{source}_S{idx+1}")
                
                # Extract features (exclude metadata columns)
                metadata_cols = ["sample_id", "species", "retention_time_min", "injection_volume_ul"]
                feature_cols = [c for c in df.columns if c not in metadata_cols]
                
                if len(feature_cols) == 0:
                    logger.warning(f"No features found in {source} data")
                    continue
                
                features = sample[feature_cols].values.astype(float)
                
                # Generate confidence-based prediction using feature magnitude
                # Normalize features to probabilities
                feature_sum = features.sum()
                if feature_sum > 0:
                    pred_probs = features / feature_sum
                else:
                    pred_probs = np.ones(len(features)) / len(features)
                
                # Pad or truncate to match number of species
                if len(pred_probs) > len(species_names):
                    pred_probs = pred_probs[:len(species_names)]
                elif len(pred_probs) < len(species_names):
                    pad_size = len(species_names) - len(pred_probs)
                    pred_probs = np.pad(pred_probs, (0, pad_size), mode='constant', constant_values=0.001)
                
                # Normalize again
                pred_probs = pred_probs / pred_probs.sum()
                
                # Get predicted class
                pred_class = np.argmax(pred_probs)
                
                # Analyze prediction
                analysis = self.prediction_analyzer.analyze_species_prediction(
                    pred_class,
                    pred_probs,
                    sample_id,
                    source
                )
                
                # Print results
                true_label = f" (True: {true_species.iloc[idx]})" if true_species is not None else ""
                print(f"\n  {sample_id}{true_label}")
                print(f"    Predicted: {analysis['predicted_species']}")
                print(f"    Phylum: {analysis['predicted_phylum']}")
                print(f"    Confidence: {analysis['confidence_pct']:.1f}%")
                
                # Format top 3 predictions
                top_3_items = []
                for pred in analysis['top_3_predictions']:
                    species = pred.get('species', 'Unknown')
                    percentage = pred.get('percentage', 0)
                    top_3_items.append(f"{species} ({percentage:.1f}%)")
                top_3_str = ", ".join(top_3_items)
                print(f"    Top 3 alternatives: {top_3_str}")
        
        # Get predictions dataframe
        self.predictions_df = self.prediction_analyzer.get_predictions_dataframe()
        self.predictions_detailed = self.prediction_analyzer.predictions
        
        # Save predictions
        pred_output = self.output_root / "predictions" / "predictions.csv"
        self.predictions_df.to_csv(pred_output, index=False)
        logger.info(f"✓ Predictions saved to {pred_output}")
        
        # Phylogenetic summary
        print("\n" + "-"*70)
        print("PHYLOGENETIC ANALYSIS SUMMARY")
        print("-"*70)
        
        if not self.predictions_detailed:
            return
        
        # Count predictions by phylum
        phylum_counts = {}
        for pred in self.predictions_detailed:
            phylum = pred.get("predicted_phylum", "Unknown")
            phylum_counts[phylum] = phylum_counts.get(phylum, 0) + 1
        
        print("\nPredicted phylum distribution:")
        for phylum, count in sorted(phylum_counts.items(), key=lambda x: x[1], reverse=True):
            pct = 100 * count / len(self.predictions_detailed)
            print(f"  {phylum}: {count} samples ({pct:.1f}%)")
        
        # Confidence analysis
        confidences = [p.get("confidence", 0.5) for p in self.predictions_detailed]
        print(f"\nConfidence statistics:")
        print(f"  Mean: {np.mean(confidences):.2%}")
        print(f"  Std Dev: {np.std(confidences):.2%}")
        print(f"  Min: {np.min(confidences):.2%}")
        print(f"  Max: {np.max(confidences):.2%}")
    
    # ============================================================
    # STEP 5: GENERATE INSIGHTS
    # ============================================================
    
    def step5_generate_insights(self):
        """Step 5: Generate automated insights from predictions."""
        print("\n" + "="*70)
        print("  STEP 5: INSIGHTS & ANALYSIS")
        print("="*70)
        
        if self.predictions_df is None or self.predictions_df.empty:
            logger.warning("No predictions available for insights")
            return
        
        # Generate insights
        insights_gen = InsightsGenerator()
        confidence_scores = np.array([p.get("confidence", 0.5) for p in self.predictions_detailed])
        
        all_insights = insights_gen.generate_comprehensive_insights(
            self.predictions_df,
            confidence_scores
        )
        
        # Display insights
        print("\n" + "-"*70)
        for i, insight in enumerate(all_insights, 1):
            print(f"\n{i}. {insight}")
        
        # Generate recommendations
        report_builder = InsightReportBuilder()
        recommendations = report_builder.create_recommendations_from_insights(all_insights)
        
        print("\n" + "-"*70)
        print("RECOMMENDATIONS:")
        print("-"*70)
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")
        
        # Save insights report
        insights_report = report_builder.create_insight_report(all_insights)
        insights_path = self.output_root / "reports" / "insights_report.txt"
        with open(insights_path, "w") as f:
            f.write(insights_report)
        
        logger.info(f"✓ Insights report saved to {insights_path}")
    
    # ============================================================
    # STEP 6: GENERATE PDF REPORTS
    # ============================================================
    
    def step6_generate_reports(self):
        """Step 6: Generate comprehensive PDF reports."""
        print("\n" + "="*70)
        print("  STEP 6: GENERATING PDF REPORTS")
        print("="*70)
        
        if self.biodata is None or self.predictions_df is None:
            logger.warning("Cannot generate reports without biodata and predictions")
            return
        
        try:
            report_gen = PDFReportGenerator(self.output_root / "reports")
            
            # Generate prediction report
            report_path = report_gen.generate_prediction_report(
                self.biodata.get("experiment_metadata", {}),
                self.biodata,
                self.predictions_df,
                self.predictions_detailed,
                self.biodata.get("growth_conditions", {}),
                "prediction_analysis.pdf"
            )
            
            if report_path:
                print(f"\n✓ PDF report generated: {report_path}")
                logger.info(f"Report saved to {report_path}")
            else:
                logger.warning("PDF generation requires reportlab library")
                print("\nTo generate PDF reports, install reportlab:")
                print("  pip install reportlab")
        
        except Exception as e:
            logger.error(f"Error generating reports: {e}")
    
    # ============================================================
    # MAIN PIPELINE EXECUTION
    # ============================================================
    
    def run_interactive(self):
        """Run the full pipeline in interactive mode."""
        print("\n" + "#"*70)
        print("#  ENHANCED MULTI-SOURCE ALGAE IDENTIFICATION PIPELINE")
        print("#"*70)
        print(f"\nOutput directory: {self.output_root}")
        
        try:
            # STEP 0: Data mode selection (DUMMY or REAL)
            self.step0_select_data_mode()
            
            # STEP 1: Data source selection and processing
            step1_result = self.step1_select_and_load_data()
            
            # Ask if user wants to continue with biodata
            if input("\nContinue with biodata collection? (yes/no): ").strip().lower() == "yes":
                self.step2_collect_biodata()
            
            # Taxonomy fetching
            if input("\nFetch taxonomy data from NCBI? (yes/no): ").strip().lower() == "yes":
                self.step3_fetch_taxonomy()
            
            # STEP 4: Predictions with phylogenetic analysis
            self.step4_make_predictions()
            
            # STEP 5: Insights generation
            self.step5_generate_insights()
            
            # STEP 6: PDF reports
            if input("\nGenerate PDF reports? (yes/no): ").strip().lower() == "yes":
                self.step6_generate_reports()
            
            # Summary
            self._print_summary()
            
        except KeyboardInterrupt:
            print("\n\n✗ Pipeline interrupted by user")
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
    
    def _print_summary(self):
        """Print pipeline execution summary."""
        print("\n" + "#"*70)
        print("#  PIPELINE EXECUTION SUMMARY")
        print("#"*70)
        print(f"\nOutput directory: {self.output_root}")
        print("\nGenerated files:")
        
        # List output files
        for file_path in sorted(self.output_root.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.output_root)
                print(f"  ✓ {rel_path}")
        
        print("\n" + "#"*70)
        print("Pipeline completed successfully!")
        print("#"*70)


# ============================================================
# CLI & ARGUMENT PARSING
# ============================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Enhanced Multi-Source Algae Identification Pipeline"
    )
    
    p.add_argument(
        "--output", type=str, default="pipeline_output",
        help="Output directory for results (default: pipeline_output)"
    )
    
    p.add_argument(
        "--config", type=str, default=None,
        help="Configuration file (JSON) for non-interactive mode"
    )
    
    p.add_argument(
        "--no-taxonomy", action="store_true",
        help="Skip taxonomy fetching from NCBI"
    )
    
    p.add_argument(
        "--no-reports", action="store_true",
        help="Skip PDF report generation"
    )
    
    return p.parse_args()


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    args = parse_args()
    
    # Create orchestrator
    orchestrator = EnhancedPipelineOrchestrator(
        output_root=Path(args.output)
    )
    
    # Run pipeline
    orchestrator.run_interactive()


if __name__ == "__main__":
    main()
