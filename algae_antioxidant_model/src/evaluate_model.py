# src/evaluate_model.py

from sklearn.metrics import r2_score, mean_squared_error
import numpy as np
import pandas as pd

def evaluate(model, X_test, y_test):
    preds = model.predict(X_test)
    if isinstance(y_test, pd.DataFrame):
        r2 = {}
        rmse = {}
        for idx, col in enumerate(y_test.columns):
            r2[col] = r2_score(y_test.iloc[:, idx], preds[:, idx])
            rmse[col] = np.sqrt(mean_squared_error(y_test.iloc[:, idx], preds[:, idx]))
        return {
            "R2": r2,
            "RMSE": rmse,
            "preds": preds
        }

    r2 = r2_score(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    return {
        "R2": r2,
        "RMSE": rmse,
        "preds": preds
    }
