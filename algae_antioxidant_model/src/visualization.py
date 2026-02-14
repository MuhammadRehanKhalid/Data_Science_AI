# src/visualization.py

import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import pandas as pd
from .config import FIGURE_DIR

def save_scatter(y_true, y_pred, target_names=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    figures_dir = os.path.join(base_dir, "..", FIGURE_DIR)
    os.makedirs(figures_dir, exist_ok=True)

    if isinstance(y_true, pd.DataFrame):
        target_names = target_names or list(y_true.columns)
        y_true_values = y_true.values
    else:
        target_names = target_names or ["ORAC"]
        y_true_values = np.asarray(y_true).reshape(-1, 1)

    y_pred_values = np.asarray(y_pred)
    if y_pred_values.ndim == 1:
        y_pred_values = y_pred_values.reshape(-1, 1)

    for idx, target in enumerate(target_names):
        yt = y_true_values[:, idx]
        yp = y_pred_values[:, idx]
        plt.scatter(yt, yp, alpha=0.6)
        plt.plot([yt.min(), yt.max()], [yt.min(), yt.max()], '--r')
        plt.xlabel(f"Observed {target}")
        plt.ylabel(f"Predicted {target}")
        plt.title(f"Observed vs Predicted {target}")
        plt.savefig(os.path.join(figures_dir, f"model_performance_{target}.png"), dpi=300)
        plt.close()
