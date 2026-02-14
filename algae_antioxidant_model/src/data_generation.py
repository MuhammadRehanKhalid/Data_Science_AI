# src/data_generation.py

import numpy as np
import pandas as pd
from .config import N_SAMPLES, RANDOM_STATE

def generate_data():
    # Only seed if RANDOM_STATE is explicitly set
    if RANDOM_STATE is not None:
        np.random.seed(RANDOM_STATE)

    algal_classes = ['Brown', 'Red', 'Green', 'Microalgae']
    solvents = ['70%EtOH', '70%MeOH', 'Acetone', 'EthylAcetate', 'Water']

    df = pd.DataFrame({
        'algal_class': np.random.choice(algal_classes, N_SAMPLES),
        'solvent': np.random.choice(solvents, N_SAMPLES),
        'phenolic_potential': np.random.uniform(0.2, 1.0, N_SAMPLES),
        'lipid_content': np.random.uniform(0.1, 0.8, N_SAMPLES),
        'polarity_index': np.random.uniform(0.1, 0.9, N_SAMPLES),
        'extraction_temp': np.random.uniform(20, 60, N_SAMPLES),
        'extraction_time': np.random.uniform(30, 180, N_SAMPLES)
    })

    phylo_map = {'Green': 1, 'Red': 2, 'Microalgae': 2.5, 'Brown': 3}
    df['phylo_score'] = df['algal_class'].map(phylo_map)

    base_score = (
        50 * df['phenolic_potential']
        + 30 * df['lipid_content']
        + 25 * df['polarity_index']
        + 20 * df['phylo_score']
        + 5 * (df['extraction_temp'] / 60)  # Temperature contribution
        + 3 * (df['extraction_time'] / 180)  # Time contribution
    )

    # ORAC
    df['ORAC'] = (
        base_score
        - abs(df['polarity_index'] - 0.6) * 15
        + np.random.normal(0, 3, N_SAMPLES)
    )

    # FRAP (reducing power)
    df['FRAP'] = (
        base_score * 0.9
        + 12 * df['phenolic_potential']
        + np.random.normal(0, 4, N_SAMPLES)
    )

    # DPPH (% inhibition, bounded 0-100)
    dpph_raw = (
        100 * (0.35 * df['phenolic_potential'] + 0.25 * df['lipid_content'] + 0.2 * df['polarity_index'])
        + 5 * df['phylo_score']
        + np.random.normal(0, 3, N_SAMPLES)
    )
    df['DPPH'] = np.clip(dpph_raw, 0, 100)

    # ABTS
    df['ABTS'] = (
        base_score * 0.8
        + 8 * df['phenolic_potential']
        + np.random.normal(0, 4, N_SAMPLES)
    )

    # Total phenolic compounds (TPC)
    df['TPC'] = (
        200 * df['phenolic_potential']
        + 15 * df['phylo_score']
        + np.random.normal(0, 6, N_SAMPLES)
    )

    print(
        f"\n📊 Generated {N_SAMPLES} samples with ORAC range: [{df['ORAC'].min():.1f}, {df['ORAC'].max():.1f}]"
    )

    return df
