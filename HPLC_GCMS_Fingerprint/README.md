# HPLC / GC-MS Fingerprint — Multi-Task Modeling Pipeline

End-to-end Python project that generates **synthetic HPLC and GC-MS
fingerprint data**, exports it to Excel, ingests it, and trains **multi-task
ML/DL models** that simultaneously predict:

| Head | Task | Output |
|------|------|--------|
| 1 | Species/phylum classification | Predicted algal species & phylum |
| 2 | Solvent-activity regression | Antioxidant activity per solvent → recommended solvent |
| 3 | Assay-performance regression | DPPH / ABTS / FRAP scores → recommended assay |

---

## Project Structure

```
HPLC_GCMS_Fingerprint/
├── data/                          ← generated Excel workbook lands here
│
├── data_generation/
│   ├── constants.py               ← species, solvents, peak layouts
│   ├── hplc_generator.py          ← HPLC peak-table dummy data
│   ├── gcms_generator.py          ← GC-MS m/z-bin dummy data
│   └── excel_exporter.py          ← multi-sheet Excel export
│
├── ingestion/
│   ├── loader.py                  ← load + validate workbook
│   ├── feature_engineering.py     ← raw / binned / binary / meta features
│   └── dataset.py                 ← MultiTaskDataset unified object
│
├── models/
│   ├── ml_baseline.py             ← sklearn RF + GBR multi-output baseline
│   └── dl_multitask.py            ← PyTorch shared encoder + 4 heads
│
├── training/
│   └── trainer.py                 ← ML and DL training loops
│
├── evaluation/
│   └── metrics.py                 ← classification + regression metrics,
│                                     recommendation logic
│
├── run_pipeline.py                ← end-to-end demo script
├── requirements.txt
└── README.md
```

---

## Quickstart

### 1 · Install dependencies

```bash
pip install -r HPLC_GCMS_Fingerprint/requirements.txt
```

> **Python 3.10+** required.  
> For GPU acceleration install a CUDA-enabled PyTorch wheel from
> [pytorch.org](https://pytorch.org/get-started/locally/).

### 2 · Run the full pipeline

```bash
# from the repository root
python -m HPLC_GCMS_Fingerprint.run_pipeline
```

Or invoke the script directly:

```bash
cd HPLC_GCMS_Fingerprint
python run_pipeline.py
```

For the terminal step navigator with back / next / status / exit, run:

```bash
python enhanced_pipeline.py
```

If you want the launcher entry point used by the repo, run:

```bash
python pipeline_launcher.py
```

### 3 · Common options

| Flag | Default | Description |
|------|---------|-------------|
| `--reps N` | 15 | Replicates per species (total samples = 6 × N) |
| `--representation` | combined | Feature repr: `raw`, `binned`, `binary`, `meta`, `combined` |
| `--epochs N` | 200 | DL training epochs |
| `--batch-size N` | 16 | DL mini-batch size |
| `--skip-dl` | off | Skip PyTorch training, run ML baseline only |
| `--output PATH` | `data/fingerprint_data.xlsx` | Excel workbook path |
| `--training-display` | `verbose` | Show full training logs or compact progress updates |

### GUI Launcher
-----------
A lightweight Tkinter GUI is available for terminal-style runs that streams console output into a window. Launch it with:

```bash
python pipeline_gui.py
```

Options in the GUI:
- Choose `Verbose` or `Progress` training display.
- Provide per-step overrides (example: `5:progress,6:verbose`).

Per-step training display
-------------------------
The pipeline supports a global training display mode and per-step overrides. Use the CLI options:

```bash
# Global compact progress bars for training
python run_pipeline.py --training-display progress

# Override step 5 (ML) and step 6 (DL) individually
python run_pipeline.py --step-display "5:progress,6:verbose"
```

Notes:
- Step numbers correspond to the pipeline steps printed at runtime (ML baseline is step 5, DL training is step 6).
- `--step-display` overrides the global `--training-display` for the specified steps.
Use `--training-display progress` if you want compact percentage-style training feedback instead of step-by-step model log lines.

Example – larger dataset, longer DL training:

```bash
python run_pipeline.py --reps 30 --epochs 500
```

### Windows executable build

If you want a Windows `.exe` for the pipeline, build it from the repository root:

```powershell
.\build_pipeline_exe.ps1
```

The terminal step navigator is the console path for step-by-step control. Use `run_pipeline.py` for the full ML/DL pipeline and `enhanced_pipeline.py` for the back / next / status / exit menu.

### Data Layout Help

If you want to prepare your own CSV files, use the schema guide in [data/source_templates/README.txt](data/source_templates/README.txt). It shows the required metadata, fingerprint columns, and target columns for FTIR, HPLC, GC-MS, and mixed-source training.

---

## Data Schema

The generated workbook `fingerprint_data.xlsx` contains four sheets:

### `HPLC_Fingerprints`

| Column | Type | Description |
|--------|------|-------------|
| `sample_id` | str | Unique ID `HPLC_XXXX` |
| `species` | str | Algal species |
| `phylum` | str | Taxonomic phylum/class |
| `replicate` | int | Replicate index |
| `intensity_RT_01` … `intensity_RT_50` | float | HPLC peak intensities at 50 fixed RT positions (AU) |
| `activity_Water`, `activity_MeOH_70`, … | float | Mean antioxidant activity (0–100) using that solvent |
| `DPPH_Water`, `ABTS_Water`, `FRAP_Water`, … | float | Per-assay activity (0–100) per solvent |

### `GCMS_Fingerprints`

Same metadata + target columns as HPLC, but instead of RT peaks uses:

| Column | Type | Description |
|--------|------|-------------|
| `intensity_mz_001` … `intensity_mz_080` | float | Summed ion intensity in 80 m/z bins (Da) |

### `Solvent_Properties`

| Column | Description |
|--------|-------------|
| `solvent_code` | Short code (e.g. `MeOH_70`) |
| `full_name` | Full solvent name |
| `polarity_index` | Empirical polarity index |
| `dielectric_constant` | Relative permittivity at 25 °C |
| `is_protic` | 1 = protic, 0 = aprotic |

### `Data_Dictionary`

Full column-level documentation (column name, dtype, units, description, source sheet).

---

## Feature Representations

The `ingestion/feature_engineering.py` module builds four complementary
representations that can be used individually or combined:

| Name | Source | Dimension | Notes |
|------|--------|-----------|-------|
| `raw` | HPLC (50) + GC-MS (80) | 130 | log1p normalised |
| `binned` | 10 RT bins + 10 m/z bins | 20 | coarser, less noisy |
| `binary` | HPLC + GC-MS | 130 | presence/absence fingerprint |
| `meta` | HPLC + GC-MS | 12 | mean, std, n_peaks, skewness, max, diversity |
| `combined` | all of the above | 292 | default; best for DL encoder |

---

## Model Architecture

### ML Baseline (`models/ml_baseline.py`)

```
X ──► StandardScaler ──► RandomForestClassifier        ──► species / phylum
                    └──► MultiOutputRegressor (GBR×6)  ──► solvent activities
                    └──► MultiOutputRegressor (GBR×3)  ──► assay performances
```

### DL Multi-Task MLP (`models/dl_multitask.py`)

```
X ──► BatchNorm ──► Dense(256) ──► ReLU ──► Dropout
                ──► Dense(128) ──► ReLU ──► Dropout
                ──► Dense(64)  ──► ReLU
                         │ Z (latent, 64-dim)
           ┌─────────────┼────────────────────┐
           ▼             ▼                    ▼
     Dense(32)→       Dense(32)→          Dense(32)→
     Softmax(n_sp)    Softmax(n_ph)       Sigmoid(n_sol)
     [CrossEntropy]   [CrossEntropy]      [MSE]
```

Joint loss = α·CE_species + β·CE_phylum + γ·MSE_solvents + δ·MSE_assays  
Default weights: α=1.0, β=0.5, γ=1.0, δ=0.8

---

## Inference / Recommendation

For any new sample the pipeline returns:

```python
{
    "predicted_species":   "Sargassum muticum",
    "best_solvent":        "MeOH_70",
    "solvent_activities":  {"Water": 0.41, "MeOH_70": 0.79, …},
    "best_assay":          "FRAP",
    "assay_performances":  {"DPPH": 0.68, "ABTS": 0.71, "FRAP": 0.81},
}
```

---

## Extending the Pipeline

* **Add new species**: edit `data_generation/constants.py`.
* **Add new solvents**: extend `SOLVENTS` and `SOLVENT_PROPS` in `constants.py`.
* **Add new assays**: extend `ASSAYS` and the bias dicts in `constants.py`.
* **Swap the DL backbone**: replace `SharedEncoder` in `models/dl_multitask.py`
  with a CNN (spectra as 2-D images) or Transformer.
* **Real data**: replace `generate_hplc()` / `generate_gcms()` with your own
  peak-table CSV reader and pass the resulting DataFrames to `export_to_excel()`.

---

## License

See [LICENSE](LICENSE) for the full terms. This project is proprietary and
all rights are reserved unless you have explicit written permission from the
copyright holder.
