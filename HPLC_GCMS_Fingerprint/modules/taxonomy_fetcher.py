# ============================================================
# NCBI TAXONOMY FETCHER MODULE
# ============================================================
"""
Fetch real taxonomy data from NCBI for algae species.
Integrates seamlessly with the HPLC/GC-MS/FTIR pipeline.
"""

from Bio import Entrez
import pandas as pd
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# REQUIRED: Set your NCBI email
Entrez.email = "m.rehankhalid786@gmail.com"  # CHANGE THIS
Entrez.api_key = None  # Optional: Add your NCBI API key for faster requests


# ============================================================
# CORE: TAXONOMY FETCHER CLASS
# ============================================================

class NCBITaxonomyFetcher:
    """Fetch and cache taxonomy data from NCBI for species."""
    
    def __init__(self, cache_file: Optional[Path] = None):
        """
        Parameters
        ----------
        cache_file : Path, optional
            Path to cache taxonomy results (CSV format).
        """
        self.cache_file = cache_file
        self.cache: Dict[str, Dict] = {}
        
        if cache_file and cache_file.exists():
            self._load_cache()
    
    def fetch_taxonomy(self, species_name: str, use_cache: bool = True) -> Dict:
        """
        Fetch taxonomy for a single species from NCBI.
        
        Parameters
        ----------
        species_name : str
            Scientific name of the species (e.g., "Chlorella vulgaris")
        use_cache : bool
            Use cached result if available.
            
        Returns
        -------
        dict
            Taxonomy data with keys: species_input, scientific_name, tax_id, 
            rank, kingdom, phylum, class, order, family, genus, status, message
        """
        
        if use_cache and species_name in self.cache:
            logger.info(f"[OK] Using cached taxonomy for {species_name}")
            return self.cache[species_name]
        
        logger.info(f"-> Fetching taxonomy for: {species_name}")
        
        try:
            # Search NCBI taxonomy database
            search_handle = Entrez.esearch(
                db="taxonomy",
                term=species_name,
                retmax=1
            )
            search_record = Entrez.read(search_handle)
            search_handle.close()
            
            if len(search_record["IdList"]) == 0:
                # Fallback: Try base name without suffixes (e.g., remove "(green)", "(orange)")
                base_name = species_name.split("(")[0].strip()
                if base_name != species_name:
                    logger.info(f"-> Fallback: Trying base name '{base_name}' after suffix removal")
                    return self.fetch_taxonomy(base_name, use_cache=use_cache)
                
                result = {
                    "species_input": species_name,
                    "status": "NOT_FOUND",
                    "message": "Species not found in NCBI taxonomy database"
                }
                self.cache[species_name] = result
                return result
            
            tax_id = search_record["IdList"][0]
            
            # Fetch detailed taxonomy record
            time.sleep(0.5)  # Be respectful to NCBI servers
            fetch_handle = Entrez.efetch(
                db="taxonomy",
                id=tax_id,
                retmode="xml"
            )
            fetch_record = Entrez.read(fetch_handle)
            fetch_handle.close()
            
            tax_data = fetch_record[0]
            
            # Extract lineage
            lineage_dict = {}
            for item in tax_data.get("LineageEx", []):
                rank = item.get("Rank", "")
                name = item.get("ScientificName", "")
                lineage_dict[rank] = name
            
            # Build result
            result = {
                "species_input": species_name,
                "scientific_name": tax_data.get("ScientificName", ""),
                "tax_id": str(tax_id),
                "rank": tax_data.get("Rank", ""),
                "kingdom": lineage_dict.get("kingdom", ""),
                "phylum": lineage_dict.get("phylum", ""),
                "class": lineage_dict.get("class", ""),
                "order": lineage_dict.get("order", ""),
                "family": lineage_dict.get("family", ""),
                "genus": lineage_dict.get("genus", ""),
                "status": "SUCCESS"
            }
            
            self.cache[species_name] = result
            logger.info(f"[OK] Successfully fetched: {result['scientific_name']} "
                       f"(Phylum: {result['phylum']})")
            
            return result
            
        except Exception as e:
            result = {
                "species_input": species_name,
                "status": "ERROR",
                "message": str(e)
            }
            logger.error(f"✗ Error fetching {species_name}: {e}")
            self.cache[species_name] = result
            return result
    
    def fetch_batch_taxonomy(self, species_list: List[str]) -> pd.DataFrame:
        """
        Fetch taxonomy for multiple species.
        
        Parameters
        ----------
        species_list : List[str]
            List of species names
            
        Returns
        -------
        pd.DataFrame
            DataFrame with taxonomy for all species
        """
        results = []
        for species in species_list:
            result = self.fetch_taxonomy(species)
            results.append(result)
            time.sleep(0.5)  # Rate limiting
        
        df = pd.DataFrame(results)
        return df
    
    def save_cache(self):
        """Save cache to CSV file."""
        if self.cache_file:
            df = pd.DataFrame(list(self.cache.values()))
            df.to_csv(self.cache_file, index=False)
            logger.info(f"[OK] Cache saved to {self.cache_file}")
    
    def _load_cache(self):
        """Load cache from CSV file."""
        if self.cache_file and self.cache_file.exists():
            df = pd.read_csv(self.cache_file)
            for _, row in df.iterrows():
                species = row["species_input"]
                self.cache[species] = row.to_dict()
            logger.info(f"[OK] Loaded {len(self.cache)} cached entries")
    
    def validate_species_names(self, species_list: List[str]) -> Dict[str, Dict]:
        """
        Validate all species names against NCBI taxonomy.
        
        Parameters
        ----------
        species_list : List[str]
            List of species names to validate
            
        Returns
        -------
        dict
            Validation results with keys:
            - 'passed': List of species that were found
            - 'failed': List of species that were NOT found
            - 'details': Full details for each species
        """
        results = {
            'passed': [],
            'failed': [],
            'details': {}
        }
        
        print("\n" + "="*70)
        print("  SPECIES NAME VALIDATION")
        print("="*70)
        print(f"\nValidating {len(species_list)} species names against NCBI...\n")
        
        for i, species in enumerate(species_list, 1):
            print(f"  [{i}/{len(species_list)}] {species}...", end=" ", flush=True)
            
            taxonomy = self.fetch_taxonomy(species, use_cache=True)
            
            if taxonomy.get('status') == 'SUCCESS':
                print("[PASS]")
                results['passed'].append(species)
                results['details'][species] = {
                    'status': 'PASS',
                    'scientific_name': taxonomy.get('scientific_name', species),
                    'phylum': taxonomy.get('phylum', 'Unknown'),
                    'tax_id': taxonomy.get('tax_id', '')
                }
            else:
                print("[FAIL]")
                results['failed'].append(species)
                results['details'][species] = {
                    'status': 'FAIL',
                    'message': taxonomy.get('message', 'Not found in NCBI taxonomy'),
                    'suggestion': self._suggest_correction(species)
                }
        
        # Print summary
        print("\n" + "="*70)
        print("  VALIDATION SUMMARY")
        print("="*70)
        print(f"\nPassed : {len(results['passed'])}/{len(species_list)}")
        print(f"Failed : {len(results['failed'])}/{len(species_list)}")
        
        if results['passed']:
            print("\n[OK] Species found in NCBI:")
            for sp in results['passed']:
                 print(f"  [OK] {sp}")
        
        if results['failed']:
            print("\n[ERROR] Species NOT found in NCBI:")
            for sp in results['failed']:
                suggestion = results['details'][sp].get('suggestion', '')
                print(f"  [FAIL] {sp}")
                if suggestion:
                    print(f"    -> Suggestion: {suggestion}")
        
        return results
    
    def _suggest_correction(self, species_name: str) -> str:
        """
        Suggest a possible correction for a misspelled species name.
        
        Parameters
        ----------
        species_name : str
            The invalid species name
            
        Returns
        -------
        str
            Suggested correction or empty string
        """
        # Try base name without parenthetical suffixes
        if '(' in species_name and ')' in species_name:
            base_name = species_name.split('(')[0].strip()
            return f"Try '{base_name}' (remove suffix)"
        
        # Try common misspellings
        common_fixes = {
            'zofingiensis': 'Check spelling: Chromochloris zofingiensis',
            'vulgaris': 'Check spelling: Chlorella vulgaris',
            'tricornutum': 'Check spelling: Phaeodactylum tricornutum',
        }
        
        for keyword, suggestion in common_fixes.items():
            if keyword in species_name.lower():
                return suggestion
        
        return ""


# ============================================================
# UTILITY: PREDICTION TAXONOMY TRACER
# ============================================================

class PredictionTaxonomyTracer:
    """
    Trace predicted species back to taxonomy and phyla.
    Works with ML/DL model predictions.
    """
    
    def __init__(self, fetcher: NCBITaxonomyFetcher):
        """
        Parameters
        ----------
        fetcher : NCBITaxonomyFetcher
            Initialized taxonomy fetcher
        """
        self.fetcher = fetcher
        self.prediction_traces: List[Dict] = []
    
    def trace_prediction(
        self,
        predicted_species: str,
        confidence: float = 1.0,
        data_source: str = "Unknown",
        sample_id: str = ""
    ) -> Dict:
        """
        Trace a prediction back to taxonomy.
        
        Parameters
        ----------
        predicted_species : str
            Predicted species name
        confidence : float
            Model confidence (0-1)
        data_source : str
            Source of prediction (FTIR, HPLC, GCMS, etc.)
        sample_id : str
            Sample identifier
            
        Returns
        -------
        dict
            Prediction trace with taxonomy and confidence
        """
        
        taxonomy = self.fetcher.fetch_taxonomy(predicted_species)
        
        trace = {
            "sample_id": sample_id,
            "data_source": data_source,
            "predicted_species": predicted_species,
            "confidence": confidence,
            "phylum": taxonomy.get("phylum", "Unknown"),
            "kingdom": taxonomy.get("kingdom", "Unknown"),
            "class": taxonomy.get("class", ""),
            "order": taxonomy.get("order", ""),
            "family": taxonomy.get("family", ""),
            "genus": taxonomy.get("genus", ""),
            "tax_id": taxonomy.get("tax_id", ""),
            "status": taxonomy.get("status", "")
        }
        
        self.prediction_traces.append(trace)
        return trace
    
    def get_traces_dataframe(self) -> pd.DataFrame:
        """Get all prediction traces as DataFrame."""
        return pd.DataFrame(self.prediction_traces)
    
    def save_traces(self, output_path: Path):
        """Save prediction traces to CSV."""
        df = self.get_traces_dataframe()
        df.to_csv(output_path, index=False)
        logger.info(f"[OK] Prediction traces saved to {output_path}")


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Initialize fetcher with caching
    cache_path = Path("taxonomy_cache.csv")
    fetcher = NCBITaxonomyFetcher(cache_file=cache_path)
    
    # Example: Fetch single species
    species_list = [
        "Chlorella vulgaris",
        "Spirulina platensis",
        "Phaeodactylum tricornutum",
    ]
    
    print("\n" + "="*60)
    print("FETCHING TAXONOMY DATA FROM NCBI")
    print("="*60)
    
    for species in species_list:
        result = fetcher.fetch_taxonomy(species)
        print(f"\n{species}:")
        print(f"  Phylum: {result.get('phylum')}")
        print(f"  Class:  {result.get('class')}")
        print(f"  Status: {result.get('status')}")
    
    # Save cache
    fetcher.save_cache()
    
    # Example: Trace predictions
    print("\n" + "="*60)
    print("TRACING PREDICTIONS WITH TAXONOMY")
    print("="*60)
    
    tracer = PredictionTaxonomyTracer(fetcher)
    
    # Simulate model predictions
    predictions = [
        ("Chlorella vulgaris", 0.92, "FTIR"),
        ("Spirulina platensis", 0.85, "HPLC"),
        ("Phaeodactylum tricornutum", 0.78, "GCMS"),
    ]
    
    for species, conf, source in predictions:
        trace = tracer.trace_prediction(species, conf, source, f"sample_{species[:3]}")
        print(f"\n{source} → {species} (confidence: {conf:.2%})")
        print(f"  Phylum: {trace['phylum']}")
        print(f"  Kingdom: {trace['kingdom']}")
    
    # Save traces
    tracer.save_traces(Path("prediction_traces.csv"))
