import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import yaml
import sys
from os import path as osp
SRC_DIR = osp.dirname(__file__)
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)
import omics_loader as ol

TARGETS = ["FRAP", "ABTS", "DPPH", "ORAC", "TPC"]

class MLP(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 1)
        )
    def forward(self, x):
        return self.net(x)


def train_one_target(df: pd.DataFrame, target: str, outdir: Path):
    num_cols = ["Extraction_Yield_mg_per_g", "Temperature_C", "Incubation_h"]
    cat_cols = ["Algal_Class", "Solvent"]
    X = df[num_cols + cat_cols]
    y = df[target].values.astype(np.float32)
    pre = ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
    ])
    pipe = Pipeline([("pre", pre)])
    Xt = pipe.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(Xt, y, test_size=0.2, random_state=42)

    X_train = torch.tensor(X_train.toarray() if hasattr(X_train, "toarray") else X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train.reshape(-1,1), dtype=torch.float32)
    X_test = torch.tensor(X_test.toarray() if hasattr(X_test, "toarray") else X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test.reshape(-1,1), dtype=torch.float32)

    model = MLP(X_train.shape[1])
    loss_fn = nn.MSELoss()
    opt = optim.Adam(model.parameters(), lr=1e-3)

    epochs = 200
    for ep in range(epochs):
        model.train()
        opt.zero_grad()
        pred = model(X_train)
        loss = loss_fn(pred, y_train)
        loss.backward()
        opt.step()
        if (ep+1) % 50 == 0:
            model.eval()
            with torch.no_grad():
                ptest = model(X_test)
                rmse = torch.sqrt(nn.MSELoss()(ptest, y_test)).item()
            print(f"{target} epoch {ep+1}: train_mse={loss.item():.2f}, test_rmse={rmse:.2f}")

    # Final evaluation
    model.eval()
    with torch.no_grad():
        ptest = model(X_test)
        ypred = ptest.numpy().reshape(-1)
        ytrue = y_test.numpy().reshape(-1)
        rmse = float(np.sqrt(np.mean((ypred - ytrue)**2)))
        mae = float(np.mean(np.abs(ypred - ytrue)))
        # R2
        ss_res = float(np.sum((ytrue - ypred)**2))
        ss_tot = float(np.sum((ytrue - np.mean(ytrue))**2))
        r2 = float(1 - ss_res/ss_tot) if ss_tot > 0 else float("nan")

    return {"target": target, "model": "MLP", "RMSE": rmse, "MAE": mae, "R2": r2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--outdir", default="reports")
    ap.add_argument("--plots", default="plots")
    ap.add_argument("--config", default="Algae_Antioxidant_Project/config.yaml")
    args = ap.parse_args()
    outdir = Path(args.outdir)
    df = pd.read_csv(args.data)
    # Optional omics integration
    cfg = {}
    if Path(args.config).exists():
        cfg = yaml.safe_load(Path(args.config).read_text())
    omics_cfg = cfg.get("omics", {})
    use_omics = omics_cfg.get("gc_ms", False) or omics_cfg.get("lc_ms", False)
    ms_file = Path(omics_cfg.get("ms_features_file", ""))
    n_components = int(omics_cfg.get("n_components", 20))
    if use_omics and ms_file.exists():
        omics = ol.load_omics(ms_file)
        merged = ol.merge_omics(df, omics)
        merged, comp_cols = ol.reduce_omics(merged, n_components=n_components)
        df = merged

    outdir.mkdir(parents=True, exist_ok=True)

    results = []
    for target in TARGETS:
        results.append(train_one_target(df, target, outdir))
    pd.DataFrame(results).to_csv(outdir / "dl_results.csv", index=False)
    print(f"Saved DL results to {outdir / 'dl_results.csv'}")


if __name__ == "__main__":
    main()
