import argparse
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(123)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True, help="Path to algae_antioxidants_dummy.csv (for SampleID alignment)")
    ap.add_argument("--out", default="data/omics_features.csv")
    ap.add_argument("--n_features", type=int, default=200)
    args = ap.parse_args()

    df = pd.read_csv(args.meta)
    # Build SampleID aligned to metadata
    df["SampleID"] = df["Algal_Class"].astype(str) + "|" + df["Solvent"].astype(str) + "|" + df["Replicate"].astype(str)

    n = len(df)
    k = args.n_features

    # Create latent factors linked to chemistry/assay patterns
    # Use Extraction_Yield and TPC as drivers for some MS features; add solvent/class signals
    yield_norm = (df["Extraction_Yield_mg_per_g"].values - df["Extraction_Yield_mg_per_g"].mean()) / (df["Extraction_Yield_mg_per_g"].std() + 1e-8)
    tpc_norm = (df["TPC"].values - df["TPC"].mean()) / (df["TPC"].std() + 1e-8)

    # Encode categorical as simple numeric effects for generating signals
    algal_map = {v:i for i,v in enumerate(sorted(df["Algal_Class"].unique()))}
    solvent_map = {v:i for i,v in enumerate(sorted(df["Solvent"].unique()))}
    algal_eff = np.array([algal_map[v] for v in df["Algal_Class"].values])
    solvent_eff = np.array([solvent_map[v] for v in df["Solvent"].values])
    algal_eff = (algal_eff - algal_eff.mean()) / (algal_eff.std() + 1e-8)
    solvent_eff = (solvent_eff - solvent_eff.mean()) / (solvent_eff.std() + 1e-8)

    # Generate feature matrix with some features highly correlated to yield/TPC and some noise
    F = np.zeros((n, k))
    for j in range(k):
        w_y = rng.uniform(0, 1)
        w_t = rng.uniform(0, 1)
        w_a = rng.uniform(0, 0.5)
        w_s = rng.uniform(0, 0.5)
        noise = rng.normal(0, 1, size=n)
        F[:, j] = 2.0*w_y*yield_norm + 2.0*w_t*tpc_norm + 1.0*w_a*algal_eff + 1.0*w_s*solvent_eff + noise
        # Make some sparse positive-only features to mimic peak areas
        if j % 5 == 0:
            F[:, j] = np.clip(F[:, j] * 50 + rng.normal(5, 2, size=n), 0, None)
        else:
            F[:, j] = np.clip(F[:, j] * 10 + rng.normal(1, 0.5, size=n), 0, None)

    cols = [f"feat_{i:04d}" for i in range(k)]
    omics = pd.DataFrame(F, columns=cols)
    omics.insert(0, "SampleID", df["SampleID"].values)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    omics.to_csv(out, index=False)
    print(f"Wrote dummy omics features: {out} shape={omics.shape}")


if __name__ == "__main__":
    main()
