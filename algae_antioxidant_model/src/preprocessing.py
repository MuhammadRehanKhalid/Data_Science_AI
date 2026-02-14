# src/preprocessing.py

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

def get_preprocessor(X):
    categorical = ['algal_class', 'solvent']
    numerical = [c for c in X.columns if c not in categorical]

    return ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical),
        ('num', 'passthrough', numerical)
    ])
