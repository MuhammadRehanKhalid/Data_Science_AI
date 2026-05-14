# ============================================================
# DATA INPUT & VALIDATION MODULE
# ============================================================
"""
Interactive data source selection and format validation.
Supports FTIR, HPLC, and GC-MS data sources.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# DATA SOURCE SPECIFICATIONS
# ============================================================

DATA_SOURCE_FORMATS = {
    "FTIR": {
        "name": "Fourier-Transform Infrared Spectroscopy",
        "extensions": [".csv", ".xlsx"],
        "required_columns": [
            "wavenumber",  # or "wavelength"
            "intensity"    # or "absorbance", "transmittance"
        ],
        "optional_columns": [
            "sample_id",
            "species",
            "phylum",
            "replicate",
            "growth_condition"
        ],
        "example_format": """
Sample FTIR CSV format:
wavenumber,intensity,sample_id,species
400.5,0.45,S001,Chlorella_vulgaris
401.0,0.48,S001,Chlorella_vulgaris
401.5,0.50,S001,Chlorella_vulgaris
...

OR Excel with sheets: "metadata" and "ftir_data"
        """,
        "note": "One row per wavenumber point per sample"
    },
    
    "HPLC": {
        "name": "High-Performance Liquid Chromatography",
        "extensions": [".csv", ".xlsx"],
        "required_columns": [
            "retention_time",  # in minutes
            "peak_area",       # or "peak_height", "intensity"
            "sample_id"
        ],
        "optional_columns": [
            "compound_name",
            "wavelength",
            "species",
            "phylum",
            "solvent",
            "replicate"
        ],
        "example_format": """
Sample HPLC CSV format:
retention_time,peak_area,sample_id,compound_name,wavelength,species
2.34,5632.1,S001,Chlorogenic_acid,254,Chlorella_vulgaris
3.45,8921.3,S001,Rutin,254,Chlorella_vulgaris
5.67,1234.2,S001,Quercetin,280,Chlorella_vulgaris
...

OR Excel with sheets: "metadata" and "hplc_peaks"
        """,
        "note": "One row per detected peak per sample"
    },
    
    "GCMS": {
        "name": "Gas Chromatography - Mass Spectrometry",
        "extensions": [".csv", ".xlsx"],
        "required_columns": [
            "retention_time",  # in minutes
            "mz_ratio",        # mass-to-charge ratio
            "intensity",
            "sample_id"
        ],
        "optional_columns": [
            "compound_name",
            "compound_formula",
            "species",
            "phylum",
            "replicate"
        ],
        "example_format": """
Sample GC-MS CSV format:
retention_time,mz_ratio,intensity,sample_id,compound_name,species
8.23,71.0,2341.5,S001,Toluene,Chlorella_vulgaris
9.45,85.0,5623.2,S001,Xylene,Chlorella_vulgaris
11.34,91.0,892.1,S001,Styrene,Chlorella_vulgaris
...

OR Excel with sheets: "metadata" and "gcms_spectra"
        """,
        "note": "One row per m/z ratio per retention time per sample"
    }
}


# ============================================================
# INTERACTIVE DATA SOURCE SELECTOR
# ============================================================

class DataSourceSelector:
    """Guide user through data source selection."""
    
    def __init__(self):
        self.selected_sources: List[str] = []
        self.source_configs: Dict[str, Dict] = {}
    
    def print_welcome(self):
        """Print welcome message with available sources."""
        print("\n" + "="*70)
        print("  MULTI-SOURCE DATA PIPELINE FOR ALGAE SPECIES IDENTIFICATION")
        print("="*70)
        print("\nAvailable Data Sources:")
        print("-" * 70)
        
        for idx, (source_key, spec) in enumerate(DATA_SOURCE_FORMATS.items(), 1):
            print(f"\n  {idx}. {source_key}")
            print(f"     → {spec['name']}")
            print(f"     → File formats: {', '.join(spec['extensions'])}")
    
    def ask_source_selection(self) -> List[str]:
        """
        Ask user which data sources they want to use.
        
        Returns
        -------
        List[str]
            Selected source keys (FTIR, HPLC, GCMS)
        """
        print("\n" + "-"*70)
        print("SELECT DATA SOURCES")
        print("-"*70)
        print("\nEnter the numbers of sources you want to use (comma-separated):")
        print("Examples:")
        print("  • '1' → FTIR only")
        print("  • '2,3' → HPLC and GC-MS")
        print("  • '1,2,3' → All three sources")
        
        while True:
            user_input = input("\nYour choice: ").strip()
            
            try:
                choices = [int(x.strip()) for x in user_input.split(",")]
                sources = []
                source_keys = list(DATA_SOURCE_FORMATS.keys())
                
                for choice in choices:
                    if 1 <= choice <= len(source_keys):
                        sources.append(source_keys[choice - 1])
                    else:
                        print(f"✗ Invalid choice: {choice}")
                        continue
                
                if sources:
                    self.selected_sources = sources
                    print(f"\n✓ Selected: {', '.join(sources)}")
                    return sources
                
            except (ValueError, IndexError):
                print("✗ Invalid input. Please enter numbers separated by commas.")
    
    def show_format_specifications(self, source: str):
        """Display format specifications for a data source."""
        spec = DATA_SOURCE_FORMATS.get(source)
        if not spec:
            return
        
        print(f"\n{'='*70}")
        print(f"  {source} DATA FORMAT")
        print(f"{'='*70}")
        print(f"\nFull Name: {spec['name']}")
        print(f"\nAccepted Formats: {', '.join(spec['extensions'])}")
        print(f"\nRequired Columns: {', '.join(spec['required_columns'])}")
        print(f"\nOptional Columns: {', '.join(spec['optional_columns'])}")
        print(f"\nFormat Example:{spec['example_format']}")
        print(f"\nNote: {spec['note']}")
    
    def ask_training_mode(self) -> str:
        """
        Ask whether to use single or multiple sources for training.
        
        Returns
        -------
        str
            'single' or 'multiple'
        """
        print("\n" + "-"*70)
        print("TRAINING MODE SELECTION")
        print("-"*70)
        print("\nHow would you like to use these data sources?")
        print("\n  1. Single Source Training")
        print("     → Train separate models for each source")
        print("     → Combine predictions using ensemble methods")
        print("     → Good for comparing source-specific performance")
        print("\n  2. Multiple Source Training (Fusion)")
        print("     → Combine all sources into unified feature matrix")
        print("     → Train single model on fused data")
        print("     → Good for improved accuracy with complementary data")
        
        while True:
            choice = input("\nYour choice (1 or 2): ").strip()
            if choice == "1":
                return "single"
            elif choice == "2":
                return "multiple"
            else:
                print("✗ Invalid choice. Enter 1 or 2.")


# ============================================================
# DATA LOADER & VALIDATOR
# ============================================================

class MultiSourceDataLoader:
    """Load and validate data from multiple sources."""
    
    def __init__(self, selected_sources: List[str]):
        """
        Parameters
        ----------
        selected_sources : List[str]
            List of selected data sources (FTIR, HPLC, GCMS)
        """
        self.sources = selected_sources
        self.data: Dict[str, pd.DataFrame] = {}
        self.metadata: Dict[str, Dict] = {}
    
    def load_source_data(
        self,
        source: str,
        file_path: Path,
        sheet_name: str = None
    ) -> pd.DataFrame:
        """
        Load data from a file for a specific source.
        
        Parameters
        ----------
        source : str
            Data source name (FTIR, HPLC, GCMS)
        file_path : Path
            Path to data file
        sheet_name : str, optional
            Sheet name for Excel files
            
        Returns
        -------
        pd.DataFrame
            Loaded data
        """
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Loading {source} data from {file_path.name}")
        
        try:
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            # Validate columns
            self._validate_columns(source, df)
            
            self.data[source] = df
            logger.info(f"✓ Loaded {len(df)} rows for {source}")
            
            return df
            
        except Exception as e:
            logger.error(f"✗ Error loading {source}: {e}")
            raise
    
    def _validate_columns(self, source: str, df: pd.DataFrame):
        """Validate required columns are present."""
        spec = DATA_SOURCE_FORMATS[source]
        required = spec["required_columns"]
        
        # Check for required columns (case-insensitive)
        df_cols_lower = [col.lower() for col in df.columns]
        missing = []
        
        for req_col in required:
            if req_col.lower() not in df_cols_lower:
                missing.append(req_col)
        
        if missing:
            raise ValueError(
                f"Missing required columns for {source}: {missing}\n"
                f"Required: {required}"
            )
    
    def load_all_sources(self, data_dir: Path) -> Dict[str, pd.DataFrame]:
        """
        Interactive loading of all selected sources.
        
        Parameters
        ----------
        data_dir : Path
            Directory containing data files
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            Loaded data for each source
        """
        
        print("\n" + "-"*70)
        print("LOADING DATA FROM SELECTED SOURCES")
        print("-"*70)
        
        for source in self.sources:
            print(f"\n{source}:")
            
            # Show available files
            spec = DATA_SOURCE_FORMATS[source]
            available_files = []
            
            for ext in spec["extensions"]:
                available_files.extend(data_dir.glob(f"*{ext}"))
            
            if not available_files:
                print(f"  ✗ No data files found in {data_dir}")
                continue
            
            print(f"  Available files:")
            for idx, file in enumerate(available_files[:5], 1):
                print(f"    {idx}. {file.name}")
            
            # Ask user which file to load
            while True:
                file_choice = input(f"  Enter file name or path for {source}: ").strip()
                file_path = Path(file_choice) if Path(file_choice).exists() else data_dir / file_choice
                
                if file_path.exists():
                    self.load_source_data(source, file_path)
                    break
                else:
                    print(f"  ✗ File not found: {file_path}")
        
        return self.data
    
    def get_unified_features(self) -> pd.DataFrame:
        """
        Create unified feature matrix from multiple sources.
        
        Returns
        -------
        pd.DataFrame
            Combined features with sample_id as index
        """
        if len(self.data) == 1:
            # Single source - return as-is
            source = list(self.data.keys())[0]
            return self.data[source]
        
        # Multiple sources - merge on sample_id
        dfs = []
        for source, df in self.data.items():
            # Ensure sample_id column exists
            if "sample_id" not in df.columns:
                logger.warning(f"{source} missing sample_id column")
                continue
            
            df_copy = df.copy()
            df_copy.columns = [f"{source}_{col}" if col != "sample_id" else col 
                              for col in df_copy.columns]
            dfs.append(df_copy)
        
        if not dfs:
            raise ValueError("No valid data to merge")
        
        # Merge on sample_id
        merged = dfs[0]
        for df in dfs[1:]:
            merged = merged.merge(df, on="sample_id", how="outer")
        
        logger.info(f"✓ Created unified feature matrix: {merged.shape}")
        return merged


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    selector = DataSourceSelector()
    selector.print_welcome()
    
    # Show format examples
    for source in ["FTIR", "HPLC", "GCMS"]:
        selector.show_format_specifications(source)
