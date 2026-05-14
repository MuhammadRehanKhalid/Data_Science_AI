# Source Combination Testing Guide

## Quick Answer: Where Are My Figures?

### Single Source: GCMS Only
```
python run_pipeline.py
→ Select: GCMS (only)
```

**Figures Generated:**
- `02_gcms_spectra.png` ← **GC-MS spectrum**
- `07_pca_biplot.png` (built from GCMS features)
- `07b_plsda_biplot.png` (built from GCMS features)
- `08a_confusion_species_ml[GCMS].png` ← **Model labeled with [GCMS]**
- `08b_confusion_phylum_ml[GCMS].png`
- `10_feature_importance.png`
- `11a_scatter_solvents_ml[GCMS].png`
- `11b_scatter_assays_ml[GCMS].png`
- `16_phylogenetic_tree.png` (if taxonomy available)

**Total: ~9 figures**

---

### Dual Source: FTIR + GCMS
```
python run_pipeline.py
→ Select: FTIR, GCMS
```

**Figures Generated:**
- `02b_ftir_spectra.png` ← **FTIR spectrum**
- `02_gcms_spectra.png` ← **GC-MS spectrum**
- `07_pca_biplot.png` (built from FTIR + GCMS features)
- `07b_plsda_biplot.png` (built from FTIR + GCMS features)
- `08a_confusion_species_ml[FTIR + GCMS].png` ← **Model labeled with [FTIR + GCMS]**
- `08b_confusion_phylum_ml[FTIR + GCMS].png`
- `10_feature_importance.png`
- `11a_scatter_solvents_ml[FTIR + GCMS].png`
- `11b_scatter_assays_ml[FTIR + GCMS].png`
- `16_phylogenetic_tree.png` (if taxonomy available)

**Total: ~14 figures**

---

### Dual Source: FTIR + HPLC
```
python run_pipeline.py
→ Select: FTIR, HPLC
```

**Figures Generated:**
- `01_hplc_chromatograms.png` ← **HPLC chromatogram**
- `02b_ftir_spectra.png` ← **FTIR spectrum**
- `03_assay_heatmap.png` (HPLC-based)
- `04_solvent_heatmap.png` (HPLC-based)
- `05_assay_boxplots.png` (HPLC-based)
- `06_solvent_barplots.png` (HPLC-based)
- `07_pca_biplot.png` (built from FTIR + HPLC features)
- `07b_plsda_biplot.png` (built from FTIR + HPLC features)
- `08a_confusion_species_ml[FTIR + HPLC].png` ← **Model labeled with [FTIR + HPLC]**
- `08b_confusion_phylum_ml[FTIR + HPLC].png`
- `10_feature_importance.png`
- `11a_scatter_solvents_ml[FTIR + HPLC].png`
- `11b_scatter_assays_ml[FTIR + HPLC].png`
- `12_radar_solvent.png` (HPLC-based)
- `13_phylum_assay_recommendation.png` (HPLC-based)
- `14_solvent_assay_interaction.png` (HPLC-based)
- `15_best_solvent_distribution.png` (HPLC-based)
- `16_phylogenetic_tree.png` (if taxonomy available)

**Total: ~17 figures**

---

## Understanding the Figure Naming

### Source-Specific Figures (Only Generated for Selected Sources)

| Figure | Requires |
|--------|----------|
| `01_hplc_chromatograms.png` | HPLC ✓ |
| `02_gcms_spectra.png` | GCMS ✓ |
| `02b_ftir_spectra.png` | FTIR ✓ |
| `03_assay_heatmap.png` | HPLC ✓ |
| `04_solvent_heatmap.png` | HPLC ✓ |
| `05_assay_boxplots.png` | HPLC ✓ |
| `06_solvent_barplots.png` | HPLC ✓ |
| `12_radar_solvent.png` | HPLC ✓ |
| `13_phylum_assay_recommendation.png` | HPLC ✓ |
| `14_solvent_assay_interaction.png` | HPLC ✓ |
| `15_best_solvent_distribution.png` | HPLC ✓ |

### Universal Model Figures (Generated Regardless of Source)

| Figure | Notes |
|--------|-------|
| `07_pca_biplot.png` | Built from selected sources |
| `07b_plsda_biplot.png` | Built from selected sources |
| `08a_confusion_species_ml[SOURCES].png` | **Labeled with source combination** |
| `08b_confusion_phylum_ml[SOURCES].png` | **Labeled with source combination** |
| `08c_confusion_species_dl[SOURCES].png` | DL model (if not skipped) |
| `08d_confusion_phylum_dl[SOURCES].png` | DL model (if not skipped) |
| `10_feature_importance.png` | From selected sources |
| `11a_scatter_solvents_ml[SOURCES].png` | **Labeled with source combination** |
| `11b_scatter_assays_ml[SOURCES].png` | **Labeled with source combination** |

---

## How to Compare Results

### Step 1: Run GCMS Only
```bash
python run_pipeline.py
# Select: GCMS only
# Note: figures_dir location and accuracy metrics
```

### Step 2: Run FTIR + GCMS
```bash
python run_pipeline.py
# Select: FTIR, GCMS
# Compare: accuracy improvement vs GCMS alone
```

### Step 3: Run FTIR + HPLC
```bash
python run_pipeline.py
# Select: FTIR, HPLC
# Compare: accuracy improvement vs single sources
```

### Step 4: Run All Three
```bash
python run_pipeline.py
# Select: FTIR, HPLC, GCMS
# Compare: accuracy with full multi-modal approach
```

### Analysis Questions to Answer:

1. **GCMS Contribution**: How much does GCMS improve models vs other sources?
2. **FTIR Benefit**: Does FTIR add new information or is it redundant?
3. **HPLC Value**: How important is HPLC chromatogram detail?
4. **Multi-Modal Synergy**: Do three sources together beat the sum of pairs?

---

## Summary Output

After each run, look for the **FIGURE GENERATION SUMMARY**:

```
======================================================================
FIGURE GENERATION SUMMARY
======================================================================
Data Sources Selected: GCMS
Source Combination: [GCMS]
Total Figures Generated: 9
Output Directory: /path/to/figures/

SOURCE-SPECIFIC FIGURES:
  • GC-MS Spectra

MODEL EVALUATION FIGURES [GCMS]:
  • PCA Biplot
  • PLS-DA Biplot
  • Confusion Matrix – Species (ML Baseline)
  • Confusion Matrix – Phylum (ML Baseline)
  ...
```

This shows **exactly** what was generated for your selected sources!

---

## Common Workflows

### Workflow 1: Find Minimal Sufficient Data
```
Run 1: HPLC only       → Baseline accuracy
Run 2: HPLC + GCMS     → Improvement?
Run 3: HPLC + FTIR     → Different improvement?
Conclusion: Choose combo that gives best accuracy-to-cost ratio
```

### Workflow 2: Assess GCMS Value
```
Run 1: HPLC only       → Baseline
Run 2: HPLC + GCMS     → Delta = GCMS value
If delta > 5% accuracy: GCMS is worth including
```

### Workflow 3: Full Multi-Modal Optimization
```
Run all 7 combinations (see compare_source_combinations.py)
Compare: accuracy, runtime, figure count
Generate: comparison report with recommendations
```

---

## Troubleshooting

**Q: I selected GCMS but still see HPLC figures**
- A: Check the figure titles. Only assay/solvent analysis figures are HPLC-only.
- A: PCA/confusion matrices are universal (use combined features).

**Q: Where are my FTIR figures?**
- A: Only appears if you selected FTIR.
- A: Look for `02b_ftir_spectra.png` (not `01_` or `02_`).

**Q: How do I know which sources trained my model?**
- A: Check confusion matrix titles: `[GCMS]`, `[FTIR + HPLC]`, etc.
- A: Check the summary output after figures are generated.

**Q: Why does GCMS-only show fewer figures than HPLC-only?**
- A: HPLC includes assay/solvent analysis (9 extra figures).
- A: Core model figures are the same for both.

---

## File Organization

```
figures/
├── 01_hplc_chromatograms.png      ← HPLC only
├── 02_gcms_spectra.png            ← GCMS only
├── 02b_ftir_spectra.png           ← FTIR only
├── 03_assay_heatmap.png           ← HPLC only
├── 04_solvent_heatmap.png         ← HPLC only
├── 07_pca_biplot.png              ← All combos
├── 08a_confusion_species_ml[GCMS].png     ← Source in title
├── 08a_confusion_species_ml[FTIR+HPLC].png ← Source in title
├── 11a_scatter_solvents_ml[FTIR+GCMS].png ← Source in title
└── 16_phylogenetic_tree.png       ← All combos
```

**Pro Tip:** Confusion matrix filenames tell you exactly which sources were used!

---

For automated testing of all combinations, run:
```bash
python compare_source_combinations.py
```

This generates a complete comparison report across all 7 source combinations!
