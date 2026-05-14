# ============================================================
# SAMPLE DATA GENERATOR
# ============================================================
"""
Generate realistic dummy data for FTIR, HPLC, and GCMS analysis.
Also provides utilities to load real data from Excel/CSV files.

Supports two modes:
- DUMMY: Generate realistic synthetic data for testing
- REAL: Load actual data from user-provided files

Usage:
    from modules.sample_data_generator import SampleDataGenerator
    
    gen = SampleDataGenerator()
    
    # Dummy mode
    ftir_data = gen.generate_ftir_data(n_samples=10)
    hplc_data = gen.generate_hplc_data(n_samples=10)
    gcms_data = gen.generate_gcms_data(n_samples=10)
    
    # Real mode
    real_data = gen.load_data_from_file("path/to/data.csv")
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generate realistic dummy data or load real data from files."""
    
    def __init__(self, random_seed: int = 42):
        """
        Parameters
        ----------
        random_seed : int
            Random seed for reproducible data generation
        """
        self.random_seed = random_seed
        np.random.seed(random_seed)
        
        # Algae species for assignment
        self.algae_species = [
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
        
        logger.info("SampleDataGenerator initialized")
    
    # ============================================================
    # MODE SELECTION
    # ============================================================
    
    @staticmethod
    def ask_data_mode() -> str:
        """
        Ask user to choose between dummy or real data mode.
        
        Returns
        -------
        str
            Either "dummy" or "real"
        """
        print("\n" + "="*70)
        print("  DATA MODE SELECTION")
        print("="*70)
        print("\nChoose data mode:")
        print("  [1] DUMMY  - Generate synthetic data for testing")
        print("  [2] REAL   - Load actual data from files")
        print("\nEnter choice (1 or 2): ", end="")
        
        while True:
            choice = input().strip()
            if choice in ["1", "2"]:
                return "dummy" if choice == "1" else "real"
            print("Invalid choice. Please enter 1 or 2: ", end="")
    
    @staticmethod
    def ask_data_file_path() -> Path:
        """
        Ask user for data file path (CSV or Excel).
        
        Returns
        -------
        Path
            Path to the data file
        """
        print("\n" + "="*70)
        print("  REAL DATA FILE SELECTION")
        print("="*70)
        print("\nSupported formats: .csv, .xlsx, .xls")
        print("Please provide the path to your data file:")
        print("Example: C:\\Data\\algae_samples.csv")
        print("\nFile path: ", end="")
        
        while True:
            file_path = Path(input().strip())
            
            if not file_path.exists():
                print(f"✗ File not found: {file_path}")
                print("Please enter a valid file path: ", end="")
                continue
            
            if file_path.suffix.lower() not in [".csv", ".xlsx", ".xls"]:
                print(f"✗ Unsupported format: {file_path.suffix}")
                print("Please provide a CSV or Excel file: ", end="")
                continue
            
            return file_path
    
    # ============================================================
    # DUMMY DATA GENERATION
    # ============================================================
    
    def generate_ftir_data(self, n_samples: int = 20) -> pd.DataFrame:
        """
        Generate realistic dummy FTIR spectroscopy data.
        
        FTIR data typically has wavenumber-intensity pairs.
        We'll generate features at key wavenumbers.
        
        Parameters
        ----------
        n_samples : int
            Number of samples to generate
        
        Returns
        -------
        pd.DataFrame
            FTIR data with columns: sample_id, wavenumbers as features, species_label
        """
        data = []
        
        # Key wavenumber regions for algae (cm^-1)
        wavenumbers = [
            1000, 1020, 1050, 1100, 1160,  # C-O stretching
            1200, 1300, 1400, 1450, 1550,  # C-H bending, N-H
            1650, 1700, 1750,               # C=O stretching
            2800, 2850, 2900, 2950, 3000,  # C-H stretching
            3200, 3300, 3400, 3500          # O-H, N-H stretching
        ]
        
        for i in range(n_samples):
            sample_id = f"FTIR_S{i+1:03d}"
            
            # Assign species
            species = np.random.choice(self.algae_species)
            
            # Generate realistic intensities (0-100% transmittance)
            # Different species have different spectral signatures
            base_spectrum = np.random.uniform(50, 90, len(wavenumbers))
            
            # Add species-specific features
            if "Chlorella" in species:
                base_spectrum[15:18] += np.random.uniform(5, 15, 3)
            elif "Spirulina" in species:
                base_spectrum[12:15] += np.random.uniform(3, 8, 3)
            elif "Phaeodactylum" in species:
                base_spectrum[10:13] += np.random.uniform(4, 10, 3)
            
            # Add noise
            spectrum = base_spectrum + np.random.normal(0, 2, len(wavenumbers))
            spectrum = np.clip(spectrum, 20, 100)  # Transmittance 0-100%
            
            row = {
                "sample_id": sample_id,
                "species": species
            }
            
            # Add spectral features
            for wn, intensity in zip(wavenumbers, spectrum):
                row[f"wn_{wn}"] = intensity
            
            data.append(row)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} FTIR samples")
        return df
    
    def generate_hplc_data(self, n_samples: int = 20) -> pd.DataFrame:
        """
        Generate realistic dummy HPLC chromatography data.
        
        HPLC data includes peak areas/heights for different compounds.
        
        Parameters
        ----------
        n_samples : int
            Number of samples to generate
        
        Returns
        -------
        pd.DataFrame
            HPLC data with pigment concentrations (chlorophyll, carotenoids, etc.)
        """
        data = []
        
        # Common algal pigments
        pigments = [
            "Chlorophyll_a",
            "Chlorophyll_b",
            "Chlorophyll_c",
            "Xanthophyll",
            "Lutein",
            "Beta_carotene",
            "Fucoxanthin"
        ]
        
        for i in range(n_samples):
            sample_id = f"HPLC_S{i+1:03d}"
            
            # Assign species
            species = np.random.choice(self.algae_species)
            
            row = {
                "sample_id": sample_id,
                "species": species,
                "retention_time_min": np.random.uniform(5, 30)  # minutes
            }
            
            # Generate pigment concentrations based on species
            if "Chlorella" in species:
                row["Chlorophyll_a"] = np.random.uniform(50, 150)
                row["Chlorophyll_b"] = np.random.uniform(20, 60)
                row["Chlorophyll_c"] = np.random.uniform(0, 10)
                row["Xanthophyll"] = np.random.uniform(10, 30)
                row["Lutein"] = np.random.uniform(15, 40)
                row["Beta_carotene"] = np.random.uniform(5, 15)
                row["Fucoxanthin"] = np.random.uniform(0, 5)
            
            elif "Spirulina" in species:
                row["Chlorophyll_a"] = np.random.uniform(80, 200)
                row["Chlorophyll_b"] = np.random.uniform(0, 10)
                row["Chlorophyll_c"] = np.random.uniform(0, 5)
                row["Xanthophyll"] = np.random.uniform(30, 80)
                row["Lutein"] = np.random.uniform(10, 25)
                row["Beta_carotene"] = np.random.uniform(20, 50)
                row["Fucoxanthin"] = np.random.uniform(0, 3)
            
            elif "Phaeodactylum" in species:
                row["Chlorophyll_a"] = np.random.uniform(40, 100)
                row["Chlorophyll_b"] = np.random.uniform(0, 5)
                row["Chlorophyll_c"] = np.random.uniform(20, 50)
                row["Xanthophyll"] = np.random.uniform(10, 30)
                row["Lutein"] = np.random.uniform(0, 10)
                row["Beta_carotene"] = np.random.uniform(5, 15)
                row["Fucoxanthin"] = np.random.uniform(40, 100)
            
            else:
                # Generic algae pigments
                for pigment in pigments:
                    row[pigment] = np.random.uniform(10, 100)
            
            data.append(row)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} HPLC samples")
        return df
    
    def generate_gcms_data(self, n_samples: int = 20) -> pd.DataFrame:
        """
        Generate realistic dummy GC-MS metabolite data.
        
        GC-MS data includes m/z ratios and peak intensities.
        
        Parameters
        ----------
        n_samples : int
            Number of samples to generate
        
        Returns
        -------
        pd.DataFrame
            GC-MS data with metabolite features
        """
        data = []
        
        # Common metabolites in algae
        metabolites = [
            "m_z_73",    # TMS-glucose
            "m_z_147",   # Fatty acid
            "m_z_217",   # Sterol
            "m_z_273",   # Lipid
            "m_z_327",   # Complex lipid
            "m_z_371"    # Glycerolipid
        ]
        
        for i in range(n_samples):
            sample_id = f"GCMS_S{i+1:03d}"
            
            # Assign species
            species = np.random.choice(self.algae_species)
            
            row = {
                "sample_id": sample_id,
                "species": species,
                "injection_volume_ul": np.random.uniform(0.1, 2.0)
            }
            
            # Generate metabolite intensities based on species
            if "Chlorella" in species:
                row["m_z_73"] = np.random.uniform(500, 1500)
                row["m_z_147"] = np.random.uniform(800, 2000)
                row["m_z_217"] = np.random.uniform(1000, 2500)
                row["m_z_273"] = np.random.uniform(600, 1800)
                row["m_z_327"] = np.random.uniform(400, 1200)
                row["m_z_371"] = np.random.uniform(300, 900)
            
            elif "Spirulina" in species:
                row["m_z_73"] = np.random.uniform(800, 2000)
                row["m_z_147"] = np.random.uniform(600, 1500)
                row["m_z_217"] = np.random.uniform(1200, 2800)
                row["m_z_273"] = np.random.uniform(800, 2200)
                row["m_z_327"] = np.random.uniform(1000, 2500)
                row["m_z_371"] = np.random.uniform(600, 1500)
            
            elif "Phaeodactylum" in species:
                row["m_z_73"] = np.random.uniform(400, 1000)
                row["m_z_147"] = np.random.uniform(1000, 2500)
                row["m_z_217"] = np.random.uniform(800, 2000)
                row["m_z_273"] = np.random.uniform(1200, 3000)
                row["m_z_327"] = np.random.uniform(600, 1500)
                row["m_z_371"] = np.random.uniform(400, 1000)
            
            else:
                # Generic metabolite intensities
                for metabolite in metabolites:
                    row[metabolite] = np.random.uniform(200, 2000)
            
            data.append(row)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} GC-MS samples")
        return df
    
    # ============================================================
    # REAL DATA LOADING
    # ============================================================
    
    @staticmethod
    def load_data_from_file(file_path: Path) -> pd.DataFrame:
        """
        Load data from CSV or Excel file.
        
        Parameters
        ----------
        file_path : Path
            Path to the data file
        
        Returns
        -------
        pd.DataFrame
            Loaded data
        """
        try:
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            logger.info(f"Loaded {len(df)} rows from {file_path.name}")
            return df
        
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    # ============================================================
    # DATA VALIDATION
    # ============================================================
    
    @staticmethod
    def validate_data_structure(df: pd.DataFrame, data_source: str) -> Tuple[bool, List[str]]:
        """
        Validate that data has required columns for the data source.
        
        Parameters
        ----------
        df : pd.DataFrame
            Data to validate
        data_source : str
            Source type: "FTIR", "HPLC", or "GCMS"
        
        Returns
        -------
        Tuple[bool, List[str]]
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for sample_id column
        if "sample_id" not in df.columns:
            errors.append("Missing required column: sample_id")
        
        # Check minimum columns
        if len(df.columns) < 3:
            errors.append(f"Data has only {len(df.columns)} columns, expected at least 3")
        
        # Source-specific checks
        if data_source == "FTIR":
            wavenumber_cols = [c for c in df.columns if "wn_" in c or "wavenumber" in c.lower()]
            if len(wavenumber_cols) < 5:
                errors.append(f"FTIR data should have multiple wavenumber columns, found {len(wavenumber_cols)}")
        
        elif data_source == "HPLC":
            pigment_cols = [c for c in df.columns if any(p in c.lower() for p in ["chlorophyll", "carotenoid", "pigment", "xanthophyll"])]
            if len(pigment_cols) == 0:
                errors.append("HPLC data should contain pigment concentration columns")
        
        elif data_source == "GCMS":
            metabolite_cols = [c for c in df.columns if any(m in c.lower() for m in ["m_z", "m/z", "metabolite", "intensity"])]
            if len(metabolite_cols) == 0:
                errors.append("GC-MS data should contain m/z or metabolite intensity columns")
        
        return len(errors) == 0, errors
    
    # ============================================================
    # DATA SUMMARY
    # ============================================================
    
    @staticmethod
    def print_data_summary(df: pd.DataFrame, source_name: str):
        """Print summary of loaded/generated data."""
        print(f"\n{source_name} Data Summary:")
        print(f"  - Samples: {len(df)}")
        print(f"  - Features: {len(df.columns)}")
        print(f"  - Columns: {', '.join(df.columns[:5])}..." if len(df.columns) > 5 else f"  - Columns: {', '.join(df.columns)}")
        
        if "species" in df.columns:
            species_counts = df["species"].value_counts()
            print(f"  - Species distribution:")
            for species, count in species_counts.items():
                print(f"      {species}: {count}")


# ============================================================
# MAIN (DEMO)
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    gen = SampleDataGenerator()
    
    # Demo: Generate dummy data
    print("\n" + "="*70)
    print("DEMO: GENERATING DUMMY DATA")
    print("="*70)
    
    ftir_df = gen.generate_ftir_data(n_samples=5)
    print("\nFTIR Data:")
    print(ftir_df.head())
    
    hplc_df = gen.generate_hplc_data(n_samples=5)
    print("\nHPLC Data:")
    print(hplc_df.head())
    
    gcms_df = gen.generate_gcms_data(n_samples=5)
    print("\nGC-MS Data:")
    print(gcms_df.head())
    
    # Print summary
    gen.print_data_summary(ftir_df, "FTIR")
    gen.print_data_summary(hplc_df, "HPLC")
    gen.print_data_summary(gcms_df, "GC-MS")
