# ============================================================
# GRAPH INSIGHTS ANALYZER MODULE
# ============================================================
"""
Analyze visualizations and extract insights from prediction graphs.
Generates automated insights from statistical patterns.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# INSIGHTS GENERATOR CLASS
# ============================================================

class InsightsGenerator:
    """Generate data-driven insights from analysis results."""
    
    def __init__(self):
        self.insights: List[str] = []
    
    # ============================================================
    # SPECIES & PHYLUM INSIGHTS
    # ============================================================
    
    def analyze_species_distribution(
        self,
        predictions_df: pd.DataFrame
    ) -> List[str]:
        """
        Analyze distribution of predicted species.
        
        Parameters
        ----------
        predictions_df : pd.DataFrame
            DataFrame with predictions
            
        Returns
        -------
        List[str]
            Insights about species distribution
        """
        insights = []
        
        if predictions_df.empty:
            return insights
        
        species_counts = predictions_df["predicted_species"].value_counts()
        total = len(predictions_df)
        
        # Most common species
        most_common = species_counts.index[0]
        most_common_pct = (species_counts.iloc[0] / total) * 100
        insights.append(
            f"Most frequently predicted species: {most_common} ({most_common_pct:.1f}% of samples)"
        )
        
        # Diversity
        unique_species = predictions_df["predicted_species"].nunique()
        insights.append(
            f"Species diversity: {unique_species} different species identified across {total} samples"
        )
        
        # Dominant species
        if most_common_pct > 70:
            insights.append(
                f"Strong dominance of {most_common}. Consider verifying if this is expected."
            )
        elif most_common_pct < 20:
            insights.append(
                f"No dominant species detected. Distribution appears diverse."
            )
        
        return insights
    
    def analyze_phylum_distribution(
        self,
        predictions_df: pd.DataFrame
    ) -> List[str]:
        """
        Analyze distribution of predicted phyla.
        
        Parameters
        ----------
        predictions_df : pd.DataFrame
            DataFrame with predictions
            
        Returns
        -------
        List[str]
            Insights about phylum distribution
        """
        insights = []
        
        if predictions_df.empty or "predicted_phylum" not in predictions_df.columns:
            return insights
        
        phylum_counts = predictions_df["predicted_phylum"].value_counts()
        
        # Phylum composition
        insights.append(
            f"Phylum composition: {', '.join([f'{p} ({c}/{len(predictions_df)})' for p, c in phylum_counts.items()])}"
        )
        
        # Monophyletic vs polyphyletic
        if len(phylum_counts) == 1:
            insights.append(
                f"All samples belong to {phylum_counts.index[0]}. Culture appears monophyletic."
            )
        elif len(phylum_counts) > 3:
            insights.append(
                "Multiple phyla detected. Investigate potential contamination or mixed cultures."
            )
        
        return insights
    
    # ============================================================
    # CONFIDENCE INSIGHTS
    # ============================================================
    
    def analyze_confidence_patterns(
        self,
        confidence_scores: np.ndarray
    ) -> List[str]:
        """
        Analyze confidence score patterns.
        
        Parameters
        ----------
        confidence_scores : np.ndarray
            Confidence scores for predictions
            
        Returns
        -------
        List[str]
            Insights about confidence patterns
        """
        insights = []
        
        if len(confidence_scores) == 0:
            return insights
        
        mean_conf = np.mean(confidence_scores)
        std_conf = np.std(confidence_scores)
        min_conf = np.min(confidence_scores)
        max_conf = np.max(confidence_scores)
        
        # Overall confidence
        if mean_conf > 0.80:
            confidence_level = "High"
            recommendation = "Results are suitable for direct use"
        elif mean_conf > 0.65:
            confidence_level = "Moderate"
            recommendation = "Consider additional validation"
        else:
            confidence_level = "Low"
            recommendation = "Recommend repeating experiments"
        
        insights.append(
            f"{confidence_level} overall confidence: {mean_conf*100:.1f}±{std_conf*100:.1f}%. "
            f"{recommendation}."
        )
        
        # Confidence range
        if max_conf - min_conf > 0.5:
            insights.append(
                f"Large confidence range ({min_conf*100:.0f}%-{max_conf*100:.0f}%). "
                f"Some predictions are more reliable than others."
            )
        
        # Outliers
        low_conf_count = np.sum(confidence_scores < 0.60)
        if low_conf_count > 0:
            low_conf_pct = (low_conf_count / len(confidence_scores)) * 100
            insights.append(
                f"{low_conf_pct:.0f}% of predictions have low confidence (<60%). "
                f"Review these samples carefully."
            )
        
        return insights
    
    # ============================================================
    # SOURCE AGREEMENT INSIGHTS
    # ============================================================
    
    def analyze_source_agreement(
        self,
        source_predictions: Dict[str, List[str]]
    ) -> List[str]:
        """
        Analyze agreement between different data sources.
        
        Parameters
        ----------
        source_predictions : Dict[str, List[str]]
            Predictions from each source: {'FTIR': [...], 'HPLC': [...], ...}
            
        Returns
        -------
        List[str]
            Insights about source agreement
        """
        insights = []
        
        if len(source_predictions) < 2:
            return insights
        
        sources = list(source_predictions.keys())
        
        # Calculate agreement rates between all source pairs
        agreements = {}
        for i, source1 in enumerate(sources):
            for source2 in sources[i+1:]:
                preds1 = source_predictions[source1]
                preds2 = source_predictions[source2]
                
                if len(preds1) != len(preds2):
                    continue
                
                agreement = np.mean([p1 == p2 for p1, p2 in zip(preds1, preds2)])
                agreements[f"{source1}-{source2}"] = agreement
        
        # Best and worst agreements
        if agreements:
            best_pair = max(agreements, key=agreements.get)
            best_agree = agreements[best_pair]
            
            insights.append(
                f"Best agreement: {best_pair} ({best_agree*100:.1f}%)"
            )
            
            if best_agree > 0.85:
                insights.append(
                    f"Sources show strong agreement. Predictions are robust."
                )
            elif best_agree > 0.70:
                insights.append(
                    f"Moderate agreement between sources. Most predictions consistent."
                )
            else:
                insights.append(
                    f"Low agreement between sources. Predictions differ significantly. "
                    f"Consider using ensemble methods."
                )
        
        return insights
    
    # ============================================================
    # REPRODUCIBILITY & QUALITY INSIGHTS
    # ============================================================
    
    def analyze_replicate_consistency(
        self,
        sample_ids: List[str],
        predictions: List[str]
    ) -> List[str]:
        """
        Analyze consistency across sample replicates.
        
        Parameters
        ----------
        sample_ids : List[str]
            Sample identifiers (may contain replicate info)
        predictions : List[str]
            Species predictions
            
        Returns
        -------
        List[str]
            Insights about replicate consistency
        """
        insights = []
        
        # Try to identify replicates by common prefix
        sample_bases = {}
        for sample_id, pred in zip(sample_ids, predictions):
            # Extract base name (before any replicate suffix)
            base = sample_id.rsplit("_", 1)[0] if "_" in sample_id else sample_id
            
            if base not in sample_bases:
                sample_bases[base] = []
            sample_bases[base].append(pred)
        
        # Check consistency
        inconsistent_groups = []
        for base, preds in sample_bases.items():
            if len(preds) > 1 and len(set(preds)) > 1:
                inconsistent_groups.append(base)
        
        if inconsistent_groups:
            insights.append(
                f"Found {len(inconsistent_groups)} sample groups with inconsistent predictions. "
                f"Review: {', '.join(inconsistent_groups[:3])}"
            )
        else:
            insights.append(
                "Replicate samples show consistent predictions. Good reproducibility."
            )
        
        return insights
    
    # ============================================================
    # COMPREHENSIVE ANALYSIS
    # ============================================================
    
    def generate_comprehensive_insights(
        self,
        predictions_df: pd.DataFrame,
        confidence_scores: Optional[np.ndarray] = None,
        source_predictions: Optional[Dict] = None
    ) -> List[str]:
        """
        Generate comprehensive insights from all available data.
        
        Parameters
        ----------
        predictions_df : pd.DataFrame
            Predictions dataframe
        confidence_scores : np.ndarray, optional
            Confidence scores
        source_predictions : Dict, optional
            Source-specific predictions
            
        Returns
        -------
        List[str]
            Comprehensive insights
        """
        
        all_insights = []
        
        # Species and phylum insights
        all_insights.extend(self.analyze_species_distribution(predictions_df))
        all_insights.extend(self.analyze_phylum_distribution(predictions_df))
        
        # Confidence insights
        if confidence_scores is not None:
            all_insights.extend(self.analyze_confidence_patterns(confidence_scores))
        
        # Source agreement insights
        if source_predictions:
            all_insights.extend(self.analyze_source_agreement(source_predictions))
        
        # Replicate consistency
        if "sample_id" in predictions_df.columns and "predicted_species" in predictions_df.columns:
            all_insights.extend(
                self.analyze_replicate_consistency(
                    predictions_df["sample_id"].tolist(),
                    predictions_df["predicted_species"].tolist()
                )
            )
        
        return all_insights


# ============================================================
# GRAPH DESCRIPTION GENERATOR
# ============================================================

class GraphDescriptionGenerator:
    """Generate meaningful descriptions for graphs."""
    
    @staticmethod
    def describe_confidence_distribution() -> str:
        """Description for confidence distribution plot."""
        return (
            "Distribution of model confidence scores across all predictions. "
            "Higher confidence values indicate more reliable species identifications. "
            "Peaks in the high confidence region (>0.8) suggest reliable predictions."
        )
    
    @staticmethod
    def describe_species_composition() -> str:
        """Description for species composition pie/bar chart."""
        return (
            "Relative abundance of different algal species predicted in the sample set. "
            "This distribution helps identify the dominant species and assess diversity."
        )
    
    @staticmethod
    def describe_source_comparison() -> str:
        """Description for multi-source prediction comparison."""
        return (
            "Comparison of species predictions from different spectroscopic sources "
            "(FTIR, HPLC, GC-MS). Agreement between sources indicates robust predictions, "
            "while disagreement may indicate need for further validation."
        )
    
    @staticmethod
    def describe_confusion_matrix() -> str:
        """Description for confusion matrix."""
        return (
            "Confusion matrix showing predicted vs. true species classifications (if test set available). "
            "Diagonal elements represent correct classifications. "
            "Off-diagonal elements indicate misclassifications between similar species."
        )
    
    @staticmethod
    def describe_roc_curve() -> str:
        """Description for ROC curve."""
        return (
            "ROC curves showing trade-off between true positive rate and false positive rate "
            "across different classification thresholds. "
            "Area under curve (AUC) indicates classifier performance."
        )
    
    @staticmethod
    def describe_feature_importance() -> str:
        """Description for feature importance plot."""
        return (
            "Feature importance scores showing which spectroscopic features are most discriminative "
            "for species identification. Top features are most useful for model predictions."
        )


# ============================================================
# INSIGHT REPORT BUILDER
# ============================================================

class InsightReportBuilder:
    """Build formatted insight reports."""
    
    @staticmethod
    def create_insight_report(insights: List[str], title: str = "Analysis Insights") -> str:
        """
        Create formatted insight report.
        
        Parameters
        ----------
        insights : List[str]
            List of insight strings
        title : str
            Report title
            
        Returns
        -------
        str
            Formatted report
        """
        
        report_lines = [
            "=" * 70,
            title.center(70),
            "=" * 70,
            ""
        ]
        
        for i, insight in enumerate(insights, 1):
            report_lines.append(f"{i}. {insight}")
            report_lines.append("")
        
        report_lines.extend([
            "-" * 70,
            "Generated by Automated Insights Analysis",
            "-" * 70
        ])
        
        return "\n".join(report_lines)
    
    @staticmethod
    def create_recommendations_from_insights(insights: List[str]) -> List[str]:
        """
        Convert insights into actionable recommendations.
        
        Parameters
        ----------
        insights : List[str]
            List of insights
            
        Returns
        -------
        List[str]
            Actionable recommendations
        """
        
        recommendations = []
        
        # Check for key phrases and generate recommendations
        insights_text = " ".join(insights).lower()
        
        if "low confidence" in insights_text or "low average confidence" in insights_text:
            recommendations.append(
                "Repeat experiments with optimized growth conditions to improve prediction confidence."
            )
        
        if "contamination" in insights_text or "mixed culture" in insights_text:
            recommendations.append(
                "Verify sample sterility and culture purity. Consider streak plating or single-cell isolation."
            )
        
        if "inconsistent" in insights_text or "reproducibility" in insights_text:
            recommendations.append(
                "Review experimental protocols and ensure consistent sample handling and preparation."
            )
        
        if "multiple phyla" in insights_text:
            recommendations.append(
                "If pure culture expected, perform additional microscopy or molecular verification."
            )
        
        if "low agreement" in insights_text or "sources differ" in insights_text:
            recommendations.append(
                "Use ensemble predictions combining multiple sources for improved reliability."
            )
        
        # Default recommendations
        if not recommendations:
            recommendations.append(
                "Results are suitable for publication or further analysis."
            )
            recommendations.append(
                "Consider additional validation studies with complementary techniques."
            )
        
        return recommendations


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    
    # Example data
    predictions_df = pd.DataFrame({
        "sample_id": ["S001", "S002", "S003", "S004", "S005"],
        "predicted_species": [
            "Chlorella vulgaris",
            "Chlorella vulgaris",
            "Spirulina platensis",
            "Chlorella vulgaris",
            "Scenedesmus obliquus"
        ],
        "predicted_phylum": [
            "Chlorophyta",
            "Chlorophyta",
            "Cyanobacteria",
            "Chlorophyta",
            "Chlorophyta"
        ]
    })
    
    confidence_scores = np.array([0.87, 0.82, 0.78, 0.91, 0.65])
    
    # Generate insights
    gen = InsightsGenerator()
    
    print("\n" + "="*70)
    print("GENERATED INSIGHTS")
    print("="*70)
    
    all_insights = gen.generate_comprehensive_insights(
        predictions_df,
        confidence_scores
    )
    
    for i, insight in enumerate(all_insights, 1):
        print(f"\n{i}. {insight}")
    
    # Create formatted report
    print("\n\n")
    report_builder = InsightReportBuilder()
    report = report_builder.create_insight_report(all_insights)
    print(report)
    
    # Generate recommendations
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    recommendations = report_builder.create_recommendations_from_insights(all_insights)
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec}")
