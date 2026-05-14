"""
Real data loader for FTIR, HPLC, and GCMS fingerprint data.

Supports loading pre-processed fingerprints (binned features) from CSV or Excel files
for all source combinations used in the multi-task pipeline.

Examples
--------
    # Load a single source
    loader = RealDataLoader(selected_sources=["HPLC"])
    data = loader.load_from_directory("./my_data/")
    
    # Load multiple sources
    loader = RealDataLoader(selected_sources=["FTIR", "HPLC", "GCMS"])
    data = loader.load_from_directory("./my_data/")
    
    # Load with specific file paths
    loader = RealDataLoader(selected_sources=["HPLC", "GCMS"])
    data = loader.load_from_files({
        "HPLC": "path/to/hplc.csv",
        "GCMS": "path/to/gcms.csv"
    })
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# EXPECTED COLUMN FORMATS FOR EACH SOURCE
# ============================================================

FINGERPRINT_SPECS = {
    "FTIR": {
        "name": "Fourier-Transform Infrared Spectroscopy",
        "feature_pattern": "wn_",  # Column names like wn_400.5, wn_401.0, etc.
        "metadata_cols": ["sample_id", "species", "phylum", "replicate"],
        "description": "Spectral wavenumber columns (wn_*) + metadata",
        "example": "wn_400.5, wn_401.0, wn_401.5, ... plus activity_<solvent>, <assay>_<solvent>",
    },
    "HPLC": {
        "name": "High-Performance Liquid Chromatography",
        "feature_pattern": "intensity_RT_",  # Columns like intensity_RT_01, intensity_RT_02, etc.
        "metadata_cols": ["sample_id", "species", "phylum", "replicate"],
        "description": "Binned retention time columns (intensity_RT_*) + metadata",
        "example": "intensity_RT_01, intensity_RT_02, ... plus activity_<solvent>, <assay>_<solvent>",
    },
    "GCMS": {
        "name": "Gas Chromatography - Mass Spectrometry",
        "feature_pattern": "intensity_mz_",  # Columns like intensity_mz_001, intensity_mz_002, etc.
        "metadata_cols": ["sample_id", "species", "phylum", "replicate"],
        "description": "Binned m/z ratio columns (intensity_mz_*) + metadata",
        "example": "intensity_mz_001, intensity_mz_002, ... plus activity_<solvent>, <assay>_<solvent>",
    }
}


# ============================================================
# REAL DATA LOADER
# ============================================================

class RealDataLoader:
    """
    Load real (not dummy) fingerprint data for FTIR, HPLC, and GCMS.
    
    Attributes
    ----------
    selected_sources : List[str]
        List of data sources to load (FTIR, HPLC, GCMS).
    data : Dict[str, pd.DataFrame]
        Loaded data for each source.
    """
    
    def __init__(self, selected_sources: List[str]):
        """
        Initialize loader for selected sources.
        
        Parameters
        ----------
        selected_sources : List[str]
            List of sources to load (e.g., ["FTIR", "HPLC", "GCMS"]).
        """
        self.selected_sources = [s.upper() for s in selected_sources]
        self.data: Dict[str, pd.DataFrame] = {}
        self._validate_sources()
    
    def _validate_sources(self):
        """Ensure all requested sources are known."""
        unknown = [s for s in self.selected_sources if s not in FINGERPRINT_SPECS]
        if unknown:
            raise ValueError(f"Unknown data sources: {unknown}. Must be in {list(FINGERPRINT_SPECS.keys())}")
    
    def print_welcome(self):
        """Print welcome message and data format guide."""
        print("\n" + "="*80)
        print("  REAL DATA LOADER – Multi-Source Fingerprint Data")
        print("="*80)
        print("\nExpected data format for each source:")
        print("-"*80)
        
        for source in self.selected_sources:
            spec = FINGERPRINT_SPECS[source]
            print(f"\n{source} ({spec['name']})")
            print(f"  Features: {spec['description']}")
            print(f"  Example:  {spec['example']}")
            print(f"  Files:    CSV (.csv) or Excel (.xlsx)")
    
    def load_from_directory(self, data_dir: Path | str) -> Dict[str, pd.DataFrame]:
        """
        Interactively load data for all selected sources from a directory.
        
        Parameters
        ----------
        data_dir : Path or str
            Directory to search for data files.
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            Loaded data for each source.
        """
        data_dir = Path(data_dir)
        if not data_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {data_dir}")
        
        print("\n" + "="*80)
        print("  LOAD DATA FOR SELECTED SOURCES")
        print("="*80)
        print(f"\nSearching in: {data_dir}")
        
        for source in self.selected_sources:
            self._load_single_source_interactive(source, data_dir)
        
        print("\n" + "-"*80)
        print(f"Loaded {len(self.data)} source(s): {', '.join(self.data.keys())}")
        return self.data
    
    def load_from_files(self, file_mapping: Dict[str, Path | str]) -> Dict[str, pd.DataFrame]:
        """
        Load data from explicit file paths.
        
        Parameters
        ----------
        file_mapping : Dict[str, Path or str]
            Mapping of source name to file path.
            E.g., {"HPLC": "data/hplc.csv", "GCMS": "data/gcms.csv"}
            
        Returns
        -------
        Dict[str, pd.DataFrame]
            Loaded data for each source.
        """
        print("\n" + "="*80)
        print("  LOAD DATA FROM SPECIFIED FILES")
        print("="*80)
        
        for source in self.selected_sources:
            if source not in file_mapping:
                logger.warning(f"No file provided for {source}, skipping.")
                continue
            
            file_path = Path(file_mapping[source])
            try:
                df = self._load_file(source, file_path)
                self.data[source] = df
            except Exception as e:
                logger.error(f"Failed to load {source} from {file_path}: {e}")
                raise
        
        print("\n" + "-"*80)
        print(f"Loaded {len(self.data)} source(s): {', '.join(self.data.keys())}")
        return self.data
    
    def _load_single_source_interactive(self, source: str, data_dir: Path) -> bool:
        """
        Interactively load a single source from the given directory.
        
        Parameters
        ----------
        source : str
            Source name (FTIR, HPLC, GCMS).
        data_dir : Path
            Directory to search in.
            
        Returns
        -------
        bool
            True if successfully loaded, False if skipped.
        """
        spec = FINGERPRINT_SPECS[source]
        
        # Find candidate files
        candidates = []
        for ext in [".csv", ".xlsx", ".xls"]:
            candidates.extend(data_dir.glob(f"*{ext}"))
        
        if not candidates:
            print(f"\n{source}: No data files found in {data_dir}")
            skip = input(f"  Skip {source}? (y/n, default: y): ").strip().lower()
            return skip != "n"
        
        print(f"\n{source}:")
        print(f"  Format: {spec['description']}")
        
        # Show available files
        print(f"  Available files:")
        for idx, f in enumerate(candidates[:10], 1):
            print(f"    {idx}. {f.name}")
        
        # Ask user to select a file
        while True:
            user_input = input(f"  Enter file name (or number 1-{len(candidates)}): ").strip()
            
            # Try to interpret as file number
            try:
                file_idx = int(user_input) - 1
                if 0 <= file_idx < len(candidates):
                    file_path = candidates[file_idx]
                    break
            except ValueError:
                pass
            
            # Try to interpret as file name or path
            if Path(user_input).exists():
                file_path = Path(user_input)
                break
            else:
                candidate = data_dir / user_input
                if candidate.exists():
                    file_path = candidate
                    break
            
            print(f"  ✗ File not found: {user_input}")
        
        try:
            df = self._load_file(source, file_path)
            self.data[source] = df
            return True
        except Exception as e:
            logger.error(f"Failed to load {source}: {e}")
            print(f"  ✗ Error: {e}")
            return False
    
    def _load_file(self, source: str, file_path: Path) -> pd.DataFrame:
        """
        Load and validate data from a single file.
        
        Parameters
        ----------
        source : str
            Source name (FTIR, HPLC, GCMS).
        file_path : Path
            Path to data file.
            
        Returns
        -------
        pd.DataFrame
            Loaded data.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Loading {source} from {file_path.name}")
        
        # Load file
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Validate structure
        self._validate_structure(source, df)
        
        # Log summary
        spec = FINGERPRINT_SPECS[source]
        feature_cols = [c for c in df.columns if c.startswith(spec["feature_pattern"])]
        print(f"  ✓ Loaded {len(df)} samples with {len(feature_cols)} features")
        
        return df
    
    def _validate_structure(self, source: str, df: pd.DataFrame):
        """
        Validate that the DataFrame has the expected structure for the source.
        
        Parameters
        ----------
        source : str
            Source name.
        df : pd.DataFrame
            Data to validate.
        """
        spec = FINGERPRINT_SPECS[source]
        
        # Check metadata columns (case-insensitive)
        df_cols_lower = {col.lower(): col for col in df.columns}
        missing_meta = []
        
        for required_col in spec["metadata_cols"]:
            if required_col.lower() not in df_cols_lower:
                missing_meta.append(required_col)
        
        if missing_meta:
            logger.warning(
                f"{source}: Missing metadata columns: {missing_meta}. "
                f"Expected: {spec['metadata_cols']}"
            )
        
        # Check for feature columns
        feature_cols = [c for c in df.columns if c.startswith(spec["feature_pattern"])]
        
        if not feature_cols:
            raise ValueError(
                f"{source}: No feature columns found with pattern '{spec['feature_pattern']}'. "
                f"Expected columns like {spec['feature_pattern']}01, {spec['feature_pattern']}02, etc."
            )
        
        logger.info(f"{source}: Found {len(feature_cols)} feature columns")
    
    def get_loaded_data(self) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Get loaded data, with None for sources that weren't loaded.
        
        Returns
        -------
        Dict[str, pd.DataFrame or None]
            Data for all selected sources, with None for missing ones.
        """
        return {source: self.data.get(source) for source in self.selected_sources}
    
    def align_samples(self) -> Dict[str, pd.DataFrame]:
        """
        Align samples across all loaded sources (remove mismatches).
        
        If multiple sources are loaded, this keeps only samples that appear
        in all sources (intersection by sample_id).
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Aligned data for all sources.
        """
        if len(self.data) <= 1:
            return self.data
        
        print("\nAligning samples across sources...")
        
        # Get common sample_ids
        all_ids = None
        for source, df in self.data.items():
            if "sample_id" in df.columns:
                ids = set(df["sample_id"].astype(str).values)
                if all_ids is None:
                    all_ids = ids
                else:
                    all_ids &= ids
                logger.info(f"{source}: {len(df)} samples")
        
        if not all_ids:
            logger.warning("No common sample_ids found across sources")
            return self.data
        
        logger.info(f"Common samples: {len(all_ids)}")
        
        # Filter each source to common samples
        aligned = {}
        for source, df in self.data.items():
            if "sample_id" in df.columns:
                df_aligned = df[df["sample_id"].astype(str).isin(all_ids)].reset_index(drop=True)
                aligned[source] = df_aligned
                logger.info(f"  {source}: {len(df_aligned)} samples after alignment")
            else:
                aligned[source] = df
        
        return aligned


# ============================================================
# HELPER FUNCTION FOR INTERACTIVE REAL DATA LOADING
# ============================================================

def prompt_for_real_data(
    selected_sources: List[str],
    default_data_dir: Optional[Path | str] = None,
) -> Dict[str, Optional[pd.DataFrame]]:
    """
    Interactively prompt user to load real data for selected sources.
    
    Parameters
    ----------
    selected_sources : List[str]
        Sources to load (FTIR, HPLC, GCMS).
    default_data_dir : Path or str, optional
        Default directory to search for files. If None, ask user.
        
    Returns
    -------
    Dict[str, pd.DataFrame or None]
        Loaded data for each source (None if not found/loaded).
    """
    loader = RealDataLoader(selected_sources)
    loader.print_welcome()
    
    # Determine data directory
    if default_data_dir is None:
        print("\n" + "="*80)
        print("  SELECT DATA DIRECTORY")
        print("="*80)
        data_dir = input("\nEnter path to data directory: ").strip()
        if not data_dir:
            logger.error("No directory specified")
            return {s: None for s in selected_sources}
    else:
        data_dir = default_data_dir
    
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        logger.error(f"Not a directory: {data_dir}")
        return {s: None for s in selected_sources}
    
    # Load data
    try:
        loader.load_from_directory(data_dir)
        result = loader.get_loaded_data()
        
        # Optionally align samples
        if len(loader.data) > 1:
            align = input("\nAlign samples across sources? (y/n, default: y): ").strip().lower()
            if align != "n":
                aligned = loader.align_samples()
                result = {s: aligned.get(s) for s in selected_sources}
        
        return result
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {s: None for s in selected_sources}


if __name__ == "__main__":
    # Example usage
    sources = ["FTIR", "HPLC", "GCMS"]
    
    loader = RealDataLoader(sources)
    loader.print_welcome()
    
    # Simulate loading from a directory
    # data = loader.load_from_directory("./data")
    # print(f"\nLoaded: {list(data.keys())}")
