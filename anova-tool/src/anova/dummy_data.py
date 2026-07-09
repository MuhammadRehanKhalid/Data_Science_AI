from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


DESIGN_SPECS = {
    "1": {"name": "One-way", "factors": [("Treatment", ["T1", "T2", "T3", "T4"])]},
    "2": {"name": "Two-way", "factors": [("Factor_A", ["A1", "A2", "A3"]), ("Factor_B", ["B1", "B2"])]},
    "3": {"name": "Three-way", "factors": [("Factor_A", ["A1", "A2"]), ("Factor_B", ["B1", "B2"]), ("Factor_C", ["C1", "C2"])]},
    "4": {"name": "Four-way", "factors": [("Factor_A", ["A1", "A2"]), ("Factor_B", ["B1", "B2"]), ("Factor_C", ["C1", "C2"]), ("Factor_D", ["D1", "D2"])]},
    "5": {"name": "CRD", "factors": [("Treatment", ["T1", "T2", "T3", "T4"])]},
    "6": {"name": "RCBD", "factors": [("Treatment", ["T1", "T2", "T3", "T4"]), ("Block", ["B1", "B2", "B3"])]},
    "7": {"name": "Split-plot", "factors": [("MainPlot", ["M1", "M2", "M3"]), ("SubPlot", ["S1", "S2", "S3"])]},
    "8": {"name": "Split-split plot", "factors": [("MainPlot", ["M1", "M2"]), ("SubPlot", ["S1", "S2"]), ("SubSubPlot", ["SS1", "SS2"])]},
    "9": {"name": "Latin Square", "factors": [("Row", ["R1", "R2", "R3", "R4"]), ("Column", ["C1", "C2", "C3", "C4"]), ("Treatment", ["T1", "T2", "T3", "T4"])]},
    "10": {"name": "Split-block", "factors": [("Block1", ["B1", "B2"]), ("Block2", ["B3", "B4"]), ("Treatment", ["T1", "T2", "T3", "T4"])]},
    "11": {"name": "Strip-split", "factors": [("Strip1", ["ST1", "ST2"]), ("Strip2", ["SP1", "SP2"]), ("SubPlot", ["P1", "P2", "P3"])]},
    "12": {"name": "Split-plot Latin Square", "factors": [("Row", ["R1", "R2", "R3", "R4"]), ("Column", ["C1", "C2", "C3", "C4"]), ("MainPlot", ["M1", "M2"]), ("SubPlot", ["S1", "S2"])]},
}


def _effect_lookup(levels, start=0.0, step=2.5):
    return {level: start + index * step for index, level in enumerate(levels)}


def _build_response(row, factor_names, response_index, rng):
    base = 50 + response_index * 12
    value = base
    for factor_name in factor_names:
        level = row[factor_name]
        level_position = sum(ord(char) for char in str(level)) % 7
        value += level_position * 1.7

    if len(factor_names) >= 2:
        value += (sum(ord(char) for char in str(row[factor_names[0]])) % 5) * (sum(ord(char) for char in str(row[factor_names[1]])) % 3) * 0.4

    if len(factor_names) >= 3:
        value += (sum(ord(char) for char in str(row[factor_names[2]])) % 4) * 0.9

    if len(factor_names) >= 4:
        value += (sum(ord(char) for char in str(row[factor_names[3]])) % 3) * 0.8

    noise_scale = 1.8 + response_index * 0.5
    return round(value + rng.normal(0, noise_scale), 3)


def generate_dummy_dataset(design_choice, rows_per_cell=4, random_state=42, response_count=2):
    if design_choice not in DESIGN_SPECS:
        raise ValueError(f"Unsupported design choice: {design_choice}")

    rng = np.random.default_rng(random_state)
    spec = DESIGN_SPECS[design_choice]
    factors = spec["factors"]
    factor_names = [factor_name for factor_name, _ in factors]
    combos = list(product(*[levels for _, levels in factors]))

    rows = []
    for combo_index, combo in enumerate(combos):
        for replicate in range(rows_per_cell):
            record = {factor_name: level for factor_name, level in zip(factor_names, combo)}
            for response_index in range(response_count):
                record[f"Response_{response_index + 1}"] = _build_response(record, factor_names, response_index, rng)
            record["Replicate"] = replicate + 1
            rows.append(record)

    df = pd.DataFrame(rows)
    ordered_columns = factor_names + ["Replicate"] + [f"Response_{index + 1}" for index in range(response_count)]
    return df[ordered_columns]


def save_dummy_dataset(df, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() in {".xlsx", ".xls"}:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="DummyData", index=False)
            pd.DataFrame({
                "Column": df.columns,
                "Description": ["Generated input template column" for _ in df.columns],
            }).to_excel(writer, sheet_name="Data_Dictionary", index=False)
    else:
        df.to_csv(output_path, index=False)

    return output_path


def generate_and_save_dummy_dataset(design_choice, output_path, rows_per_cell=4, random_state=42, response_count=2):
    df = generate_dummy_dataset(design_choice, rows_per_cell=rows_per_cell, random_state=random_state, response_count=response_count)
    saved_path = save_dummy_dataset(df, output_path)
    return df, saved_path
