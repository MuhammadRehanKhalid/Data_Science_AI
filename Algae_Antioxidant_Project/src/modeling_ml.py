import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from pathlib import Path
import yaml
import sys
from os import path as osp
# Allow running as a script by adding src to sys.path for imports
SRC_DIR = osp.dirname(__file__)
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)
import omics_loader as ol
import seaborn as sns
import matplotlib.pyplot as plt
import shap

TARGETS = ["FRAP", "ABTS", "DPPH", "ORAC", "TPC"]


def build_preprocessor(df: pd.DataFrame, extra_num: list[str] | None = None):
    num_cols = ["Extraction_Yield_mg_per_g", "Temperature_C", "Incubation_h"]
    cat_cols = ["Algal_Class", "Solvent"]
    if extra_num:
        num_cols = num_cols + list(extra_num)
    pre = ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
    ])
    return pre, num_cols + cat_cols


def evaluate(y_true, y_pred):
    return {
        "R2": r2_score(y_true, y_pred),
        "RMSE": mean_squared_error(y_true, y_pred, squared=False),
        "MAE": mean_absolute_error(y_true, y_pred),
    }


def train_models(df: pd.DataFrame, outdir: Path, plots: Path, config_path: Path | None = None):
    outdir.mkdir(parents=True, exist_ok=True)
    plots.mkdir(parents=True, exist_ok=True)
    # Load config
    extra_num = []
    if config_path and Path(config_path).exists():
        cfg = yaml.safe_load(Path(config_path).read_text())
        omics_cfg = cfg.get("omics", {})
        use_omics = omics_cfg.get("gc_ms", False) or omics_cfg.get("lc_ms", False)
        ms_file = Path(omics_cfg.get("ms_features_file", ""))
        n_components = int(omics_cfg.get("n_components", 20))
        if use_omics and ms_file.exists():
            omics = ol.load_omics(ms_file)
            merged = ol.merge_omics(df, omics)
            merged, comp_cols = ol.reduce_omics(merged, n_components=n_components)
            df = merged
            extra_num = comp_cols
    pre, used_cols = build_preprocessor(df, extra_num=extra_num)

    results = []
    feature_list = used_cols

    for target in TARGETS:
        X = df[feature_list]
        y = df[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {
            "ElasticNet": ElasticNet(alpha=0.1, l1_ratio=0.3, random_state=42),
            "RandomForest": RandomForestRegressor(n_estimators=250, random_state=42),
            "XGBoost": xgb.XGBRegressor(n_estimators=400, max_depth=4, learning_rate=0.06, subsample=0.9, colsample_bytree=0.9, random_state=42)
        }

        for name, model in models.items():
            pipe = Pipeline([
                ("pre", pre),
                ("model", model)
            ])
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            metrics = evaluate(y_test, y_pred)
            metrics.update({"target": target, "model": name})
            results.append(metrics)

            # Parity plot
            plt.figure(figsize=(5,5))
            sns.scatterplot(x=y_test, y=y_pred)
            lims = [0, max(100, float(max(y_test.max(), y_pred.max())))]
            plt.plot(lims, lims, 'r--', alpha=0.6)
            plt.xlabel(f"Actual {target}")
            plt.ylabel(f"Predicted {target}")
            plt.title(f"Parity: {name} ({target})")
            plt.tight_layout()
            plt.savefig(plots / f"parity_{name}_{target}.png", dpi=200)
            plt.close()

            # SHAP importance for XGBoost
            if name == "XGBoost":
                # Compute SHAP values on transformed test data
                Xtr_test = pre.fit_transform(X_test)
                # Build feature names from preprocessor
                num_names = pre.transformers_[0][2]
                cat_enc = pre.transformers_[1][1]
                cat_names = pre.transformers_[1][2]
                # Obtain one-hot feature names
                cat_feature_names = list(cat_enc.get_feature_names_out(cat_names))
                feature_names = list(num_names) + cat_feature_names

                explainer = shap.TreeExplainer(model)
                shap_vals = explainer.shap_values(Xtr_test)
                # Summary plot
                shap.summary_plot(shap_vals, Xtr_test, feature_names=feature_names, show=False)
                plt.tight_layout()
                plt.savefig(plots / f"shap_summary_{target}.png", dpi=200)
                plt.close()
                # Bar plot of mean |SHAP|
                shap_abs = np.mean(np.abs(shap_vals), axis=0)
                idx = np.argsort(shap_abs)[::-1][:20]
                plt.figure(figsize=(8,6))
                sns.barplot(x=shap_abs[idx], y=[feature_names[i] for i in idx], orient='h')
                plt.title(f"Top SHAP features ({target})")
                plt.xlabel("Mean |SHAP|")
                plt.ylabel("Feature")
                plt.tight_layout()
                plt.savefig(plots / f"shap_bar_{target}.png", dpi=200)
                plt.close()

    res_df = pd.DataFrame(results)
    res_df.to_csv(outdir / "ml_results.csv", index=False)
    print(f"Saved ML results to {outdir / 'ml_results.csv'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--outdir", default="reports")
    ap.add_argument("--plots", default="plots")
    ap.add_argument("--config", default="Algae_Antioxidant_Project/config.yaml")
    args = ap.parse_args()
    df = pd.read_csv(args.data)
    train_models(df, Path(args.outdir), Path(args.plots), Path(args.config))


if __name__ == "__main__":
    main()
