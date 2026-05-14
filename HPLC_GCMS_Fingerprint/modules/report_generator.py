# ============================================================
# PDF REPORT GENERATOR MODULE
# ============================================================
"""
Generate comprehensive PDF reports with predictions, recommendations, and analysis.
Includes biodata, predictions, and recommendations based on confidence.
"""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: Uses reportlab for PDF generation (install: pip install reportlab)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        PageBreak, Image
    )
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not installed. PDF generation disabled.")


# ============================================================
# PDF REPORT GENERATOR CLASS
# ============================================================

class PDFReportGenerator:
    """Generate professional PDF reports for prediction analysis."""
    
    def __init__(self, output_dir: Path = None):
        """
        Parameters
        ----------
        output_dir : Path, optional
            Directory to save PDF reports
        """
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        
        if not HAS_REPORTLAB:
            logger.warning("PDF generation requires reportlab library")
            logger.warning("Install with: pip install reportlab")
    
    def generate_prediction_report(
        self,
        experiment_metadata: Dict,
        biodata: Dict,
        predictions_df: pd.DataFrame,
        predictions_detailed: List[Dict],
        growth_conditions: Dict = None,
        output_filename: str = None
    ) -> Optional[Path]:
        """
        Generate comprehensive prediction report.
        
        Parameters
        ----------
        experiment_metadata : dict
            Experiment metadata (experiment_id, date, researcher, etc.)
        biodata : dict
            Complete biodata collection
        predictions_df : pd.DataFrame
            Predictions dataframe with sample_id, predicted_species, etc.
        predictions_detailed : List[Dict]
            Detailed predictions from analyzer
        growth_conditions : dict, optional
            Growth conditions summary
        output_filename : str, optional
            Custom output filename
            
        Returns
        -------
        Path or None
            Path to generated PDF, or None if reportlab not available
        """
        
        if not HAS_REPORTLAB:
            return None
        
        # Create filename
        if not output_filename:
            exp_id = experiment_metadata.get("experiment_id", "report")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"prediction_report_{exp_id}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2e5090'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # ============================================================
        # PAGE 1: TITLE & EXPERIMENT METADATA
        # ============================================================
        
        elements.append(Paragraph("ALGAE SPECIES IDENTIFICATION REPORT", title_style))
        elements.append(Paragraph("Multi-Source Spectroscopic Analysis", styles['Heading3']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Experiment info table
        meta_data = [
            ["Experiment ID:", experiment_metadata.get("experiment_id", "N/A")],
            ["Date:", experiment_metadata.get("date", "N/A")],
            ["Researcher:", experiment_metadata.get("researcher_name", "N/A")],
            ["Institution:", experiment_metadata.get("institution", "N/A")],
            ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ]
        
        meta_table = Table(meta_data, colWidths=[2.5*inch, 3.5*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6f2ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(meta_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Objectives
        if experiment_metadata.get("objectives"):
            elements.append(Paragraph("Objectives:", heading_style))
            elements.append(Paragraph(
                experiment_metadata["objectives"],
                styles['BodyText']
            ))
            elements.append(Spacer(1, 0.2*inch))
        
        # ============================================================
        # PAGE 2: GROWTH CONDITIONS
        # ============================================================
        
        elements.append(PageBreak())
        elements.append(Paragraph("Growth Conditions", heading_style))
        
        if growth_conditions:
            condition_data = [["Parameter", "Value"]]
            for key, value in growth_conditions.items():
                if value:
                    # Format key nicely
                    param_name = key.replace("_", " ").title()
                    condition_data.append([param_name, str(value)])
            
            condition_table = Table(condition_data, colWidths=[3*inch, 3*inch])
            condition_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5090')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            elements.append(condition_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # ============================================================
        # PAGE 3: PREDICTIONS SUMMARY
        # ============================================================
        
        elements.append(PageBreak())
        elements.append(Paragraph("Prediction Results", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Create predictions table
        if not predictions_df.empty:
            pred_display = predictions_df[["sample_id", "predicted_species",
                                          "predicted_phylum", "confidence_pct"]].copy()
            pred_display["Confidence"] = pred_display["confidence_pct"].apply(lambda x: f"{x:.1f}%")
            pred_display = pred_display.drop(columns=["confidence_pct"])
            
            pred_data = [["Sample ID", "Species", "Phylum", "Confidence"]]
            for _, row in pred_display.iterrows():
                pred_data.append([
                    str(row["sample_id"])[:15],
                    str(row["predicted_species"])[:20],
                    str(row["predicted_phylum"])[:15],
                    str(row["Confidence"])
                ])
            
            pred_table = Table(pred_data, colWidths=[1.5*inch, 1.8*inch, 1.5*inch, 1.2*inch])
            pred_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5090')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            elements.append(pred_table)
            elements.append(Spacer(1, 0.3*inch))
        
        # ============================================================
        # RECOMMENDATIONS
        # ============================================================
        
        elements.append(Paragraph("Analysis & Recommendations", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary statistics
        if predictions_detailed:
            avg_confidence = sum(p.get("confidence", 0) for p in predictions_detailed) / len(predictions_detailed)
            high_conf_count = sum(1 for p in predictions_detailed if p.get("confidence", 0) > 0.75)
            low_conf_count = sum(1 for p in predictions_detailed if p.get("confidence", 0) < 0.60)
            
            summary_text = f"""
            <b>Summary Statistics:</b><br/>
            • Total Samples Analyzed: {len(predictions_detailed)}<br/>
            • Average Confidence: {avg_confidence*100:.1f}%<br/>
            • High Confidence Predictions (>75%): {high_conf_count}<br/>
            • Low Confidence Predictions (<60%): {low_conf_count}<br/>
            <br/>
            """
            
            elements.append(Paragraph(summary_text, styles['BodyText']))
        
        # Recommendations
        recommendations = self._generate_recommendations(predictions_detailed)
        elements.append(Paragraph("<b>Recommendations:</b><br/>", styles['BodyText']))
        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(f"• {rec}", styles['BodyText']))
        
        # ============================================================
        # BUILD PDF
        # ============================================================
        
        try:
            doc.build(elements)
            logger.info(f"✓ PDF report generated: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"✗ Error generating PDF: {e}")
            return None
    
    def _generate_recommendations(self, predictions: List[Dict]) -> List[str]:
        """
        Generate recommendations based on predictions.
        
        Parameters
        ----------
        predictions : List[Dict]
            List of prediction analyses
            
        Returns
        -------
        List[str]
            Recommendations
        """
        
        recommendations = []
        
        if not predictions:
            return ["Insufficient data for recommendations."]
        
        # Analyze confidence levels
        confidences = [p.get("confidence", 0) for p in predictions]
        avg_confidence = sum(confidences) / len(confidences)
        
        if avg_confidence > 0.80:
            recommendations.append(
                "High overall prediction confidence. Results are suitable for further analysis."
            )
        elif avg_confidence > 0.60:
            recommendations.append(
                "Moderate prediction confidence. Recommend validation with additional replicates."
            )
        else:
            recommendations.append(
                "Low average confidence. Recommend repeating experiments or using alternative methods."
            )
        
        # Check for diverse phyla
        phyla = set(p.get("predicted_phylum", "") for p in predictions)
        if len(phyla) > 1:
            recommendations.append(
                f"Multiple phyla detected: {', '.join(sorted(phyla))}. "
                "Ensure samples are properly labeled and identified."
            )
        
        # Growth conditions
        recommendations.append(
            "Ensure all growth conditions were maintained consistently across all samples."
        )
        
        # Next steps
        recommendations.append(
            "Consider cross-validation with molecular methods (DNA barcoding) for high-value samples."
        )
        
        return recommendations
    
    def generate_graph_report(
        self,
        graph_paths: List[Path],
        graph_descriptions: List[str] = None,
        insights: List[str] = None,
        output_filename: str = None
    ) -> Optional[Path]:
        """
        Generate report with graphs and insights.
        
        Parameters
        ----------
        graph_paths : List[Path]
            Paths to graph/image files
        graph_descriptions : List[str], optional
            Descriptions for each graph
        insights : List[str], optional
            Key insights from analysis
        output_filename : str, optional
            Custom output filename
            
        Returns
        -------
        Path or None
            Path to generated PDF
        """
        
        if not HAS_REPORTLAB:
            return None
        
        # Create filename
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"graph_report_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=1
        )
        
        elements.append(Paragraph("ANALYSIS GRAPHS & INSIGHTS", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Add insights if provided
        if insights:
            elements.append(Paragraph("<b>Key Insights:</b>", styles['Heading2']))
            for insight in insights:
                elements.append(Paragraph(f"• {insight}", styles['BodyText']))
            elements.append(Spacer(1, 0.3*inch))
        
        # Add graphs
        for idx, graph_path in enumerate(graph_paths):
            if not Path(graph_path).exists():
                logger.warning(f"Graph file not found: {graph_path}")
                continue
            
            try:
                # Add description if provided
                if graph_descriptions and idx < len(graph_descriptions):
                    elements.append(Paragraph(
                        f"<b>Figure {idx+1}: {graph_descriptions[idx]}</b>",
                        styles['Heading3']
                    ))
                
                # Add image
                img = Image(str(graph_path), width=6*inch, height=4*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
                
                # Add page break between graphs
                if idx < len(graph_paths) - 1:
                    elements.append(PageBreak())
                    
            except Exception as e:
                logger.error(f"Error adding graph {graph_path}: {e}")
        
        # Build PDF
        try:
            doc.build(elements)
            logger.info(f"✓ Graph report generated: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"✗ Error generating graph report: {e}")
            return None


# ============================================================
# REPORT CONTENT BUILDER
# ============================================================

class ReportContentBuilder:
    """Build structured content for reports."""
    
    @staticmethod
    def create_executive_summary(
        total_samples: int,
        species_identified: List[str],
        confidence_metrics: Dict
    ) -> str:
        """Create executive summary text."""
        
        summary = f"""
        This report documents the spectroscopic analysis of {total_samples} algae samples.
        
        Key Findings:
        • Number of species identified: {len(set(species_identified))}
        • Most common species: {max(set(species_identified), key=species_identified.count)}
        • Overall average confidence: {confidence_metrics.get('avg_confidence', 0)*100:.1f}%
        
        All analysis was conducted according to standard protocols with proper
        quality control measures in place.
        """
        
        return summary
    
    @staticmethod
    def create_methodology_section() -> str:
        """Create methodology section."""
        
        methodology = """
        <b>Methodology:</b>
        
        This analysis uses machine learning models trained on spectroscopic fingerprints
        to identify algal species. The models are trained on:
        
        1. FTIR (Fourier-Transform Infrared Spectroscopy)
           - Captures functional group vibrations
           - Non-destructive technique
        
        2. HPLC (High-Performance Liquid Chromatography)
           - Separates and quantifies bioactive compounds
           - Peak retention times and areas used as features
        
        3. GC-MS (Gas Chromatography - Mass Spectrometry)
           - Identifies volatile metabolites
           - m/z ratios and retention times used as features
        
        Predictions are made using ensemble methods combining results from individual
        spectroscopic techniques for improved accuracy.
        """
        
        return methodology


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    
    if not HAS_REPORTLAB:
        print("reportlab library not installed.")
        print("Install with: pip install reportlab")
    else:
        # Example: Generate prediction report
        generator = PDFReportGenerator(Path("output/reports"))
        
        experiment_meta = {
            "experiment_id": "EXP_20250514_001",
            "date": "2025-05-14",
            "researcher_name": "Dr. John Doe",
            "institution": "Research University",
            "objectives": "Identify algae species from spectroscopic data"
        }
        
        growth_cond = {
            "temperature_celsius": 25.0,
            "ph": 7.5,
            "light_intensity_umol": 150,
            "cultivation_days": 14
        }
        
        # Dummy predictions
        pred_df = pd.DataFrame({
            "sample_id": ["S001", "S002"],
            "predicted_species": ["Chlorella vulgaris", "Spirulina platensis"],
            "predicted_phylum": ["Chlorophyta", "Cyanobacteria"],
            "confidence_pct": [85.5, 78.2]
        })
        
        pred_detailed = [
            {"confidence": 0.855, "predicted_species": "Chlorella vulgaris"},
            {"confidence": 0.782, "predicted_species": "Spirulina platensis"}
        ]
        
        # Generate report
        report_path = generator.generate_prediction_report(
            experiment_meta,
            {},
            pred_df,
            pred_detailed,
            growth_cond
        )
        
        if report_path:
            print(f"✓ Report generated: {report_path}")
