import argparse
import numpy as np
import pandas as pd

ALGAL_CLASSES = [
    "Green (Chlorophyta)", "Red (Rhodophyta)", "Brown (Phaeophyceae)",
    "Cyanobacteria", "Diatoms", "Dinoflagellates", "Other microalgae"
]
SOLVENTS = [
    "Water", "70% Methanol", "70% Ethanol", "Ethyl Acetate",
    "50% Acetonitrile", "100% Acetone"
]
ASSAYS = ["FRAP", "DPPH", "ORAC", "ABTS", "TPC"]

# Relative polarity scale (approximate, higher extracts more phenolics/TPC)
SOLVENT_POLARITY = {
    "Water": 1.0,
    "70% Methanol": 0.85,
    "70% Ethanol": 0.8,
    "Ethyl Acetate": 0.5,
    "50% Acetonitrile": 0.7,
    "100% Acetone": 0.6,
}

# Class baseline antioxidant capacity (per assay) to simulate phylogenetic differences
CLASS_BASELINES = {
    "Green (Chlorophyta)": 0.75,
    "Red (Rhodophyta)": 0.85,
    "Brown (Phaeophyceae)": 0.95,
    "Cyanobacteria": 0.6,
    "Diatoms": 0.7,
    "Dinoflagellates": 0.65,
    "Other microalgae": 0.68,
}

rng = np.random.default_rng(42)


def generate(n_reps: int = 10) -> pd.DataFrame:
    rows = []
    for algal in ALGAL_CLASSES:
        class_base = CLASS_BASELINES[algal]
        for solvent in SOLVENTS:
            polarity = SOLVENT_POLARITY[solvent]
            # Simulate extraction yield (mg/g)
            yield_mean = 20 * polarity * (0.8 + 0.4 * class_base)  # scale by class
            yield_sd = 3.0
            for rep in range(n_reps):
                extraction_yield = rng.normal(yield_mean, yield_sd)
                extraction_yield = max(0, extraction_yield)
                # Assay signals correlated with yield and class baseline
                # Map yield (0-?) to normalized [0,1] capacity then scale per-assay
                norm_cap = np.tanh(extraction_yield / 25)
                # Introduce solvent preference biases per assay
                assay_bias = {
                    "FRAP": 1.0 * (0.9 + 0.2 * polarity),
                    "ABTS": 1.0 * (0.9 + 0.15 * polarity),
                    "DPPH": 1.0 * (0.85 + 0.1 * polarity),
                    "ORAC": 1.0 * (0.8 + 0.25 * (1 - polarity)),  # more non-polar sensitive
                    "TPC": 1.0 * (1.0 + 0.3 * polarity),
                }
                base = norm_cap * (0.7 + 0.6 * class_base)
                measures = {}
                for assay in ASSAYS:
                    mu = 100 * base * assay_bias[assay]  # pseudo-units, max ~100
                    sd = 8.0
                    val = rng.normal(mu, sd)
                    val = max(0, min(100, val))
                    measures[assay] = val
                rows.append({
                    "Algal_Class": algal,
                    "Solvent": solvent,
                    "Replicate": rep + 1,
                    "Extraction_Yield_mg_per_g": extraction_yield,
                    **measures
                })
    df = pd.DataFrame(rows)
    # Add simple metadata
    df["Temperature_C"] = rng.choice([20, 25, 30], size=len(df))
    df["Incubation_h"] = rng.choice([2, 6, 12, 24], size=len(df))
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/algae_antioxidants_dummy.csv")
    ap.add_argument("--reps", type=int, default=12)
    args = ap.parse_args()
    df = generate(args.reps)
    out = args.out
    pd.DataFrame(df).to_csv(out, index=False)
    print(f"Wrote dummy dataset: {out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
