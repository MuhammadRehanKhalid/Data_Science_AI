"""
Validate all algae species names against NCBI taxonomy database.

This script checks if all species defined in the project can be found on NCBI.
It helps catch typos and incorrect scientific names before running the pipeline.

Usage:
    python validate_species_names.py                 # Validate all species
    python validate_species_names.py --species "Chromochloris zofingiensis"  # Validate one species
    python validate_species_names.py --export results.csv  # Export results to CSV
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd

# Ensure project root is on sys.path
_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from HPLC_GCMS_Fingerprint.data_generation.constants import SPECIES, PHYLA
from HPLC_GCMS_Fingerprint.modules.taxonomy_fetcher import NCBITaxonomyFetcher


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    p = argparse.ArgumentParser(
        description="Validate algae species names against NCBI taxonomy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_species_names.py                    # Validate all species
  python validate_species_names.py --species "Chlorella vulgaris"  # Single species
  python validate_species_names.py --export results.csv  # Save results to file
        """
    )
    
    p.add_argument(
        "--species", type=str, default=None,
        help="Validate a single species (optional). If not provided, validates all species."
    )
    
    p.add_argument(
        "--export", type=str, default=None,
        help="Export validation results to CSV file."
    )
    
    p.add_argument(
        "--cache", type=str, default="HPLC_GCMS_Fingerprint/data/taxonomy_cache.csv",
        help="Path to taxonomy cache file (default: HPLC_GCMS_Fingerprint/data/taxonomy_cache.csv)."
    )
    
    return p.parse_args()


def main():
    """Run species name validation."""
    args = parse_args()
    
    # Initialize fetcher
    cache_path = Path(args.cache) if args.cache else None
    fetcher = NCBITaxonomyFetcher(cache_file=cache_path)
    
    # Determine species to validate
    if args.species:
        species_to_validate = [args.species]
    else:
        species_to_validate = SPECIES
    
    # Run validation
    results = fetcher.validate_species_names(species_to_validate)
    
    # Export results if requested
    if args.export:
        export_path = Path(args.export)
        
        # Create detailed results dataframe
        export_data = []
        for species, details in results['details'].items():
            row = {
                'species': species,
                'status': details['status'],
                'phylum': PHYLA.get(species, 'Unknown') if details['status'] == 'PASS' else details.get('message', ''),
            }
            
            if details['status'] == 'PASS':
                row['scientific_name'] = details.get('scientific_name', '')
                row['tax_id'] = details.get('tax_id', '')
                row['suggestion'] = ''
            else:
                row['scientific_name'] = ''
                row['tax_id'] = ''
                row['suggestion'] = details.get('suggestion', '')
            
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        df.to_csv(export_path, index=False)
        print(f"\n[OK] Results exported to: {export_path}")
    
    # Exit with appropriate code
    sys.exit(0 if len(results['failed']) == 0 else 1)


if __name__ == '__main__':
    main()
