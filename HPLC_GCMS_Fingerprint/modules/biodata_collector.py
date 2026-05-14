# ============================================================
# BIODATA COLLECTION MODULE
# ============================================================
"""
Interactive collection of growth conditions and biodata for algae samples.
Stores data in structured JSON and CSV formats.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# BIODATA SCHEMA
# ============================================================

BIODATA_SCHEMA = {
    "experiment_metadata": {
        "experiment_id": "str - Unique identifier for this experiment run",
        "date": "str - Date of experiment (YYYY-MM-DD)",
        "researcher_name": "str - Name of researcher conducting experiment",
        "institution": "str - Research institution",
        "objectives": "str - Objectives/goals of this study",
        "notes": "str - Additional notes"
    },
    
    "growth_conditions": {
        "temperature_celsius": "float - Growth temperature (°C)",
        "ph": "float - Culture pH",
        "light_intensity_umol": "float - Light intensity (μmol/m²/s)",
        "light_duration_hours": "float - Daily light duration (hours)",
        "photoperiod": "str - Light/dark cycle (e.g., '16:8')",
        "agitation_rpm": "float - Shaker/stirrer speed (RPM)",
        "culture_volume_ml": "float - Culture volume (mL)",
        "cultivation_days": "float - Number of days cultivated",
        "cultivation_type": "str - Type (batch, fed-batch, continuous, etc.)"
    },
    
    "medium_and_nutrients": {
        "medium_type": "str - Culture medium type (e.g., BG-11, f/2, custom)",
        "nitrogen_source": "str - Nitrogen source and concentration",
        "phosphorus_source": "str - Phosphorus source and concentration",
        "carbon_source": "str - Carbon source (CO2, etc.)",
        "vitamin_supplementation": "str - Vitamins added (if any)",
        "mineral_enrichment": "str - Trace elements or minerals added"
    },
    
    "environmental_conditions": {
        "aeration": "str - Aeration method/rate",
        "co2_percentage": "float - CO2 in air stream (%)",
        "humidity_if_applicable": "float - Humidity (%) if relevant",
        "contamination_assessment": "str - Any visible contamination observed?",
        "sterility_method": "str - Method used to maintain sterility"
    },
    
    "sample_collection": {
        "sample_id": "str - Unique sample identifier",
        "species_name": "str - Scientific name of species",
        "collection_day": "float - Day of culture collected",
        "cell_density_od": "float - Optical density (OD) at collection",
        "cell_density_cells_ml": "float - Cell density (cells/mL) if measured",
        "viability_percent": "float - Cell viability (%) if determined",
        "extraction_method": "str - Method used to prepare samples for analysis",
        "extraction_solvent": "str - Extraction solvent used (for HPLC/GCMS)"
    }
}


# ============================================================
# BIODATA COLLECTOR CLASS
# ============================================================

class BiodataCollector:
    """Interactively collect and manage biodata."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Parameters
        ----------
        output_dir : Path, optional
            Directory to save biodata files
        """
        self.output_dir = output_dir or Path("biodata")
        self.output_dir.mkdir(exist_ok=True)
        
        self.biodata: Dict = {
            "experiment_metadata": {},
            "growth_conditions": {},
            "medium_and_nutrients": {},
            "environmental_conditions": {},
            "samples": []
        }
    
    def print_welcome(self):
        """Print welcome message."""
        print("\n" + "="*70)
        print("  BIODATA & GROWTH CONDITIONS COLLECTION")
        print("="*70)
        print("\nThis tool will collect detailed information about your algae cultures")
        print("to ensure complete reproducibility and analysis traceability.")
    
    def collect_experiment_metadata(self):
        """Collect experiment-level metadata."""
        print("\n" + "-"*70)
        print("EXPERIMENT METADATA")
        print("-"*70)
        
        self.biodata["experiment_metadata"] = {
            "experiment_id": input("Experiment ID (e.g., 'EXP_20250514_001'): ").strip(),
            "date": input("Date (YYYY-MM-DD) [default: today]: ").strip() or datetime.now().strftime("%Y-%m-%d"),
            "researcher_name": input("Your name: ").strip(),
            "institution": input("Institution: ").strip(),
            "objectives": input("Research objectives: ").strip(),
            "notes": input("Additional notes: ").strip()
        }
        
        print("\n✓ Experiment metadata recorded")
    
    def collect_growth_conditions(self):
        """Collect growth condition parameters."""
        print("\n" + "-"*70)
        print("GROWTH CONDITIONS")
        print("-"*70)
        print("\nEnter values. Press Enter to skip optional fields.\n")
        
        self.biodata["growth_conditions"] = {
            "temperature_celsius": self._get_float("Temperature (°C): "),
            "ph": self._get_float("Culture pH: "),
            "light_intensity_umol": self._get_float("Light intensity (μmol/m²/s): "),
            "light_duration_hours": self._get_float("Daily light duration (hours): "),
            "photoperiod": input("Photoperiod (e.g., '16:8' for 16h light/8h dark): ").strip(),
            "agitation_rpm": self._get_float("Agitation speed (RPM): "),
            "culture_volume_ml": self._get_float("Culture volume (mL): "),
            "cultivation_days": self._get_float("Days of cultivation: "),
            "cultivation_type": input("Cultivation type (batch/fed-batch/continuous): ").strip()
        }
        
        print("\n✓ Growth conditions recorded")
    
    def collect_medium_and_nutrients(self):
        """Collect medium and nutrient information."""
        print("\n" + "-"*70)
        print("MEDIUM & NUTRIENTS")
        print("-"*70)
        print("\nEnter values. Press Enter to skip optional fields.\n")
        
        self.biodata["medium_and_nutrients"] = {
            "medium_type": input("Culture medium (e.g., 'BG-11', 'f/2'): ").strip(),
            "nitrogen_source": input("Nitrogen source and concentration: ").strip(),
            "phosphorus_source": input("Phosphorus source and concentration: ").strip(),
            "carbon_source": input("Carbon source (e.g., 'CO2 5%'): ").strip(),
            "vitamin_supplementation": input("Vitamins added (if any): ").strip(),
            "mineral_enrichment": input("Trace elements or minerals: ").strip()
        }
        
        print("\n✓ Medium and nutrients recorded")
    
    def collect_environmental_conditions(self):
        """Collect environmental parameters."""
        print("\n" + "-"*70)
        print("ENVIRONMENTAL CONDITIONS")
        print("-"*70)
        print("\nEnter values. Press Enter to skip optional fields.\n")
        
        self.biodata["environmental_conditions"] = {
            "aeration": input("Aeration method/rate: ").strip(),
            "co2_percentage": self._get_float("CO2 in air stream (%): "),
            "humidity_if_applicable": self._get_float("Humidity (%) if applicable: "),
            "contamination_assessment": input("Any visible contamination? (yes/no/describe): ").strip(),
            "sterility_method": input("Sterility maintenance method: ").strip()
        }
        
        print("\n✓ Environmental conditions recorded")
    
    def collect_sample_data(self) -> Dict:
        """
        Collect data for a single sample.
        
        Returns
        -------
        dict
            Sample biodata
        """
        print("\n" + "-"*70)
        print("SAMPLE INFORMATION")
        print("-"*70)
        print("\nEnter sample details. Press Enter to skip optional fields.\n")
        
        sample = {
            "sample_id": input("Sample ID (e.g., 'S_EXP_001'): ").strip(),
            "species_name": input("Species name (scientific): ").strip(),
            "collection_day": self._get_float("Collection day of culture: "),
            "cell_density_od": self._get_float("Cell density OD (@ 680nm typically): "),
            "cell_density_cells_ml": self._get_float("Cell density (cells/mL): "),
            "viability_percent": self._get_float("Cell viability (%): "),
            "extraction_method": input("Extraction method used: ").strip(),
            "extraction_solvent": input("Extraction solvent: ").strip()
        }
        
        return sample
    
    def add_sample(self):
        """Add a sample to the collection."""
        sample = self.collect_sample_data()
        self.biodata["samples"].append(sample)
        print(f"\n✓ Sample '{sample['sample_id']}' added")
    
    def add_multiple_samples(self, n_samples: int):
        """
        Add multiple samples.
        
        Parameters
        ----------
        n_samples : int
            Number of samples to collect
        """
        for i in range(n_samples):
            print(f"\n{'='*70}")
            print(f"  SAMPLE {i+1}/{n_samples}")
            print(f"{'='*70}")
            self.add_sample()
    
    def save_biodata(self, format: str = "json") -> Path:
        """
        Save biodata to file.
        
        Parameters
        ----------
        format : str
            Output format: 'json' or 'csv'
            
        Returns
        -------
        Path
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_id = self.biodata["experiment_metadata"].get("experiment_id", "unknown")
        
        if format == "json":
            output_path = self.output_dir / f"biodata_{exp_id}_{timestamp}.json"
            with open(output_path, "w") as f:
                json.dump(self.biodata, f, indent=2)
            logger.info(f"✓ Biodata saved to {output_path}")
            
        elif format == "csv":
            # Save experiment metadata
            meta_df = pd.DataFrame([self.biodata["experiment_metadata"]])
            meta_path = self.output_dir / f"biodata_metadata_{exp_id}_{timestamp}.csv"
            meta_df.to_csv(meta_path, index=False)
            
            # Save samples
            samples_df = pd.DataFrame(self.biodata["samples"])
            samples_path = self.output_dir / f"biodata_samples_{exp_id}_{timestamp}.csv"
            samples_df.to_csv(samples_path, index=False)
            
            logger.info(f"✓ Biodata saved to {meta_path} and {samples_path}")
            output_path = meta_path
        
        return output_path
    
    def get_biodata_summary(self) -> str:
        """
        Get a text summary of collected biodata.
        
        Returns
        -------
        str
            Formatted summary
        """
        summary = []
        summary.append("\n" + "="*70)
        summary.append("  BIODATA SUMMARY")
        summary.append("="*70)
        
        # Experiment metadata
        summary.append("\nEXPERIMENT:")
        for key, value in self.biodata["experiment_metadata"].items():
            if value:
                summary.append(f"  • {key}: {value}")
        
        # Growth conditions
        summary.append("\nGROWTH CONDITIONS:")
        for key, value in self.biodata["growth_conditions"].items():
            if value:
                summary.append(f"  • {key}: {value}")
        
        # Samples
        summary.append(f"\nSAMPLES: {len(self.biodata['samples'])} samples collected")
        for sample in self.biodata["samples"]:
            summary.append(f"  • {sample['sample_id']} - {sample['species_name']}")
        
        return "\n".join(summary)
    
    @staticmethod
    def _get_float(prompt: str) -> Optional[float]:
        """Get float input from user."""
        while True:
            user_input = input(prompt).strip()
            if not user_input:
                return None
            try:
                return float(user_input)
            except ValueError:
                print("✗ Please enter a valid number")


# ============================================================
# BIODATA MANAGER
# ============================================================

class BiodataManager:
    """Load and manage existing biodata files."""
    
    @staticmethod
    def load_biodata(file_path: Path) -> Dict:
        """
        Load biodata from JSON file.
        
        Parameters
        ----------
        file_path : Path
            Path to biodata JSON file
            
        Returns
        -------
        dict
            Loaded biodata
        """
        with open(file_path, "r") as f:
            biodata = json.load(f)
        logger.info(f"✓ Loaded biodata from {file_path}")
        return biodata
    
    @staticmethod
    def merge_biodata_with_predictions(
        biodata: Dict,
        predictions_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge biodata with prediction results.
        
        Parameters
        ----------
        biodata : dict
            Biodata dictionary
        predictions_df : pd.DataFrame
            Predictions with sample_id
            
        Returns
        -------
        pd.DataFrame
            Merged data
        """
        samples_df = pd.DataFrame(biodata["samples"])
        merged = predictions_df.merge(samples_df, on="sample_id", how="left")
        
        logger.info(f"✓ Merged biodata with predictions: {merged.shape}")
        return merged


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Create and use collector
    collector = BiodataCollector(Path("output/biodata"))
    collector.print_welcome()
    
    # Collect experiment data
    collector.collect_experiment_metadata()
    collector.collect_growth_conditions()
    collector.collect_medium_and_nutrients()
    collector.collect_environmental_conditions()
    
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
    
    collector.add_multiple_samples(n_samples)
    
    # Save and display summary
    collector.save_biodata("json")
    collector.save_biodata("csv")
    print(collector.get_biodata_summary())
