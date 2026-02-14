# src/train_model.py

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
import joblib
import os
import pandas as pd

from .config import TEST_SIZE, RANDOM_STATE, MODEL_DIR
from .preprocessing import get_preprocessor

def train(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    base_model = HistGradientBoostingRegressor(
        max_depth=12,
        learning_rate=0.05,
        max_iter=1000,  # More iterations for better training
        warm_start=True,
        random_state=RANDOM_STATE
    )

    is_multioutput = isinstance(y, pd.DataFrame) or (
        hasattr(y, "ndim") and getattr(y, "ndim") == 2 and getattr(y, "shape", [0, 0])[1] > 1
    )

    model = MultiOutputRegressor(base_model) if is_multioutput else base_model

    pipeline = Pipeline([
        ('prep', get_preprocessor(X)),
        ('model', model)
    ])

    pipeline.fit(X_train, y_train)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(base_dir, "..", MODEL_DIR)
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(pipeline, os.path.join(model_dir, "model.joblib"))

    return pipeline, X_test, y_test
