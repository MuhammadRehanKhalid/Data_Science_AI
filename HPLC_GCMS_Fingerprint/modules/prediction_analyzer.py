# ============================================================
# ENHANCED PREDICTION MODULE WITH TAXONOMY TRACING
# ============================================================
"""
Enhance model predictions with taxonomy information and confidence scoring.
Supports multi-source predictions with traceability.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# PREDICTION ANALYZER CLASS
# ============================================================

class PredictionAnalyzer:
    """
    Analyze and enhance model predictions with confidence and probability scores.
    """
    
    def __init__(self, species_names: List[str], phyla_mapping: Dict[str, str]):
        """
        Parameters
        ----------
        species_names : List[str]
            List of all species in training set (ordered by class label)
        phyla_mapping : Dict[str, str]
            Mapping of species names to phyla (e.g., {'Chlorella vulgaris': 'Chlorophyta'})
        """
        self.species_names = species_names
        self.phyla_mapping = phyla_mapping
        
        # Create phyla list for reference
        self.phyla_list = sorted(set(phyla_mapping.values()))
        
        self.predictions: List[Dict] = []
    
    def analyze_species_prediction(
        self,
        pred_class: int,
        pred_probabilities: np.ndarray,
        sample_id: str = "",
        data_source: str = "Combined"
    ) -> Dict:
        """
        Analyze species classification prediction.
        
        Parameters
        ----------
        pred_class : int
            Predicted class index
        pred_probabilities : np.ndarray
            Probability scores for all classes (shape: [n_species])
        sample_id : str
            Sample identifier
        data_source : str
            Source of prediction (FTIR, HPLC, GCMS, Combined)
            
        Returns
        -------
        dict
            Detailed prediction analysis
        """
        
        # Get top predictions
        top_indices = np.argsort(pred_probabilities)[::-1][:3]
        
        predicted_species = self.species_names[pred_class]
        predicted_phylum = self.phyla_mapping.get(predicted_species, "Unknown")
        
        # Build top predictions list
        top_predictions = []
        for idx in top_indices:
            species = self.species_names[idx]
            probability = float(pred_probabilities[idx])
            phylum = self.phyla_mapping.get(species, "Unknown")
            
            top_predictions.append({
                "rank": len(top_predictions) + 1,
                "species": species,
                "phylum": phylum,
                "probability": probability,
                "percentage": probability * 100
            })
        
        analysis = {
            "sample_id": sample_id,
            "data_source": data_source,
            "predicted_species": predicted_species,
            "predicted_phylum": predicted_phylum,
            "confidence": float(pred_probabilities[pred_class]),
            "confidence_pct": float(pred_probabilities[pred_class]) * 100,
            "top_3_predictions": top_predictions,
            "entropy": float(self._calculate_entropy(pred_probabilities))
        }
        
        self.predictions.append(analysis)
        return analysis
    
    def analyze_multi_source_predictions(
        self,
        predictions_dict: Dict[str, Tuple[int, np.ndarray]],
        sample_id: str = ""
    ) -> Dict:
        """
        Analyze predictions from multiple sources and create ensemble.
        
        Parameters
        ----------
        predictions_dict : Dict[str, Tuple[int, np.ndarray]]
            Dictionary mapping source name to (class_idx, probabilities)
            Example: {
                'FTIR': (0, array([0.8, 0.1, 0.1])),
                'HPLC': (0, array([0.7, 0.2, 0.1])),
                'GCMS': (1, array([0.3, 0.6, 0.1]))
            }
        sample_id : str
            Sample identifier
            
        Returns
        -------
        dict
            Multi-source ensemble analysis
        """
        
        # Collect individual predictions
        source_predictions = {}
        all_probs = []
        
        for source, (pred_class, pred_probs) in predictions_dict.items():
            species = self.species_names[pred_class]
            phylum = self.phyla_mapping.get(species, "Unknown")
            
            source_predictions[source] = {
                "species": species,
                "phylum": phylum,
                "confidence": float(pred_probs[pred_class])
            }
            all_probs.append(pred_probs)
        
        # Calculate ensemble prediction (average probabilities)
        ensemble_probs = np.mean(all_probs, axis=0)
        ensemble_class = np.argmax(ensemble_probs)
        ensemble_species = self.species_names[ensemble_class]
        ensemble_phylum = self.phyla_mapping.get(ensemble_species, "Unknown")
        
        # Check agreement
        agreement_count = sum(
            1 for src_pred in source_predictions.values()
            if src_pred["species"] == ensemble_species
        )
        agreement_pct = (agreement_count / len(source_predictions)) * 100
        
        analysis = {
            "sample_id": sample_id,
            "ensemble_species": ensemble_species,
            "ensemble_phylum": ensemble_phylum,
            "ensemble_confidence": float(ensemble_probs[ensemble_class]),
            "ensemble_confidence_pct": float(ensemble_probs[ensemble_class]) * 100,
            "source_agreement_pct": agreement_pct,
            "source_agreement_count": f"{agreement_count}/{len(source_predictions)}",
            "source_predictions": source_predictions,
            "all_sources_agree": agreement_count == len(source_predictions)
        }
        
        return analysis
    
    def get_predictions_dataframe(self) -> pd.DataFrame:
        """
        Get all predictions as DataFrame.
        
        Returns
        -------
        pd.DataFrame
            Predictions with all details
        """
        df = pd.DataFrame(self.predictions)
        
        # Expand top_3_predictions column
        top3_data = []
        for _, row in df.iterrows():
            for rank, pred in enumerate(row["top_3_predictions"]):
                top3_data.append({
                    "sample_id": row["sample_id"],
                    "rank": pred["rank"],
                    "species": pred["species"],
                    "phylum": pred["phylum"],
                    "probability": pred["probability"]
                })
        
        # Keep main predictions
        main_cols = ["sample_id", "data_source", "predicted_species",
                     "predicted_phylum", "confidence", "confidence_pct"]
        
        return df[main_cols]
    
    @staticmethod
    def _calculate_entropy(probabilities: np.ndarray) -> float:
        """
        Calculate Shannon entropy of probability distribution.
        Low entropy = confident prediction, High entropy = uncertain.
        
        Parameters
        ----------
        probabilities : np.ndarray
            Probability scores
            
        Returns
        -------
        float
            Shannon entropy
        """
        # Avoid log(0)
        probs_safe = np.where(probabilities > 0, probabilities, 1e-10)
        return float(-np.sum(probs_safe * np.log2(probs_safe)))


# ============================================================
# PHYLUM PREDICTOR CLASS
# ============================================================

class PhylumPredictor:
    """
    Predict phylum from species predictions.
    Useful for cases where phylum prediction is more stable than species.
    """
    
    def __init__(self, phyla_mapping: Dict[str, str]):
        """
        Parameters
        ----------
        phyla_mapping : Dict[str, str]
            Mapping of species names to phyla
        """
        self.phyla_mapping = phyla_mapping
        self.species_to_phylum_probs: Dict[str, Dict[str, float]] = self._create_mapping()
    
    def _create_mapping(self) -> Dict[str, Dict[str, float]]:
        """Create reverse mapping from species to phylum."""
        mapping = {}
        phyla_set = set(self.phyla_mapping.values())
        
        for species, phylum in self.phyla_mapping.items():
            mapping[species] = {p: (1.0 if p == phylum else 0.0) for p in phyla_set}
        
        return mapping
    
    def predict_phylum_from_species_probabilities(
        self,
        species_probabilities: np.ndarray,
        species_names: List[str]
    ) -> Tuple[str, float]:
        """
        Predict phylum by marginalizing over species probabilities.
        
        Parameters
        ----------
        species_probabilities : np.ndarray
            Probability distribution over species
        species_names : List[str]
            List of species names (matching order of probabilities)
            
        Returns
        -------
        Tuple[str, float]
            Most likely phylum and its probability
        """
        
        phyla_probs = {}
        
        for species, prob in zip(species_names, species_probabilities):
            phylum = self.phyla_mapping.get(species, "Unknown")
            phyla_probs[phylum] = phyla_probs.get(phylum, 0.0) + prob
        
        best_phylum = max(phyla_probs, key=phyla_probs.get)
        best_prob = phyla_probs[best_phylum]
        
        return best_phylum, float(best_prob)


# ============================================================
# PREDICTION CONFIDENCE ASSESSOR
# ============================================================

class ConfidenceAssessor:
    """Assess confidence and reliability of predictions."""
    
    # Confidence thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.75
    MEDIUM_CONFIDENCE_THRESHOLD = 0.60
    
    # Entropy thresholds (bits)
    LOW_ENTROPY_THRESHOLD = 1.0  # Confident
    HIGH_ENTROPY_THRESHOLD = 3.0  # Uncertain
    
    @staticmethod
    def assess_confidence(
        confidence: float,
        entropy: float,
        agreement_pct: Optional[float] = None
    ) -> Dict:
        """
        Assess confidence level and recommendation.
        
        Parameters
        ----------
        confidence : float
            Model confidence (0-1)
        entropy : float
            Shannon entropy of probability distribution
        agreement_pct : float, optional
            Agreement percentage for multi-source (0-100)
            
        Returns
        -------
        dict
            Confidence assessment with recommendation
        """
        
        # Base assessment on confidence
        if confidence >= ConfidenceAssessor.HIGH_CONFIDENCE_THRESHOLD:
            confidence_level = "HIGH"
        elif confidence >= ConfidenceAssessor.MEDIUM_CONFIDENCE_THRESHOLD:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"
        
        # Consider entropy
        if entropy < ConfidenceAssessor.LOW_ENTROPY_THRESHOLD:
            entropy_assessment = "Confident (Low entropy)"
        elif entropy < ConfidenceAssessor.HIGH_ENTROPY_THRESHOLD:
            entropy_assessment = "Uncertain (Medium entropy)"
        else:
            entropy_assessment = "Very Uncertain (High entropy)"
        
        # Recommendation
        if confidence_level == "HIGH" and entropy < ConfidenceAssessor.LOW_ENTROPY_THRESHOLD:
            recommendation = "✓ Prediction is reliable. Can proceed with confidence."
        elif confidence_level in ["HIGH", "MEDIUM"]:
            if agreement_pct and agreement_pct >= 80:
                recommendation = "✓ Moderate confidence. Sources mostly agree. Proceed carefully."
            else:
                recommendation = "⚠ Moderate confidence. Consider additional analysis."
        else:
            recommendation = "✗ Low confidence. Recommendation: repeat experiment or use alternative methods."
        
        return {
            "confidence_level": confidence_level,
            "confidence_score": confidence,
            "entropy": entropy,
            "entropy_assessment": entropy_assessment,
            "source_agreement_pct": agreement_pct,
            "recommendation": recommendation
        }


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Example species and phyla
    species_names = ["Chlorella vulgaris", "Spirulina platensis", "Phaeodactylum tricornutum"]
    phyla_mapping = {
        "Chlorella vulgaris": "Chlorophyta",
        "Spirulina platensis": "Cyanobacteria",
        "Phaeodactylum tricornutum": "Bacillariophyta"
    }
    
    # Initialize analyzer
    analyzer = PredictionAnalyzer(species_names, phyla_mapping)
    
    # Example: Single source prediction
    print("\n" + "="*70)
    print("SINGLE SOURCE PREDICTION EXAMPLE")
    print("="*70)
    
    pred_probs = np.array([0.75, 0.20, 0.05])
    analysis = analyzer.analyze_species_prediction(
        pred_class=0,
        pred_probabilities=pred_probs,
        sample_id="FTIR_S001",
        data_source="FTIR"
    )
    
    print(f"Predicted: {analysis['predicted_species']} ({analysis['predicted_phylum']})")
    print(f"Confidence: {analysis['confidence_pct']:.1f}%")
    print(f"Entropy: {analysis['entropy']:.2f} bits")
    
    # Example: Multi-source ensemble
    print("\n" + "="*70)
    print("MULTI-SOURCE ENSEMBLE EXAMPLE")
    print("="*70)
    
    predictions = {
        "FTIR": (0, np.array([0.75, 0.20, 0.05])),
        "HPLC": (0, np.array([0.80, 0.15, 0.05])),
        "GCMS": (1, np.array([0.20, 0.70, 0.10]))
    }
    
    ensemble = analyzer.analyze_multi_source_predictions(predictions, "S001")
    
    print(f"Ensemble: {ensemble['ensemble_species']} ({ensemble['ensemble_phylum']})")
    print(f"Agreement: {ensemble['source_agreement_pct']:.0f}%")
    print(f"Confidence: {ensemble['ensemble_confidence_pct']:.1f}%")
