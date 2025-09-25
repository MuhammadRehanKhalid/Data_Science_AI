"""
generate_data.py
Functions to generate dummy Nanodrop, UV-Vis and Fluorescence EEM datasets.
"""
import numpy as np
import pandas as pd

def gaussian(x, mu, sigma, amp):
    return amp * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

# Nanodrop generation (returns long dataframe and summary)
def generate_nanodrop_samples():
    wavelengths = np.linspace(200, 350, 151)
    samples = [
        {"sample_id": "DNA_sample_1", "type": "dsDNA", "peaks": [(230, 30, 15), (260, 50, 6), (280, 15, 6)], "noise": 0.003},
        {"sample_id": "RNA_sample_1", "type": "RNA",  "peaks": [(230, 25, 15), (260, 60, 6), (280, 12, 6)], "noise": 0.004},
        {"sample_id": "protein_contaminated", "type": "mixed", "peaks": [(230, 20, 20), (260, 30, 6), (280, 40, 6)], "noise": 0.006},
    ]
    rows = []
    summary = []
    for s in samples:
        spec = np.zeros_like(wavelengths)
        for mu, amp, sigma in s["peaks"]:
            spec += gaussian(wavelengths, mu, sigma, amp)
        baseline = 0.0008 * (wavelengths - wavelengths.min())
        noise = np.random.normal(0, s["noise"], size=wavelengths.shape)
        absorbance = spec + baseline + noise
        for wl, a in zip(wavelengths, absorbance):
            rows.append({"sample_id": s["sample_id"], "type": s["type"], "wavelength_nm": float(wl), "absorbance": float(a)})
        A260 = float(np.interp(260, wavelengths, absorbance))
        A280 = float(np.interp(280, wavelengths, absorbance))
        factor = 50.0 if s["type"]=="dsDNA" else (40.0 if s["type"]=="RNA" else 50.0)
        conc = A260 * factor
        ratio = A260 / A280 if A280 != 0 else float('nan')
        summary.append({"sample_id": s["sample_id"], "type": s["type"], "A260": A260, "A280": A280, "ratio_260_280": ratio, "conc_ng_per_uL": conc})
    return pd.DataFrame(rows), pd.DataFrame(summary)

def generate_uvvis():
    wavelengths = np.linspace(200, 800, 601)
    samples = [
        {"sample_id": "protein_sample", "peaks": [(280, 1.0, 6)], "noise": 0.002},
        {"sample_id": "chromophore_sample", "peaks": [(430, 0.8, 10), (260, 0.2, 6)], "noise": 0.003},
        {"sample_id": "blank_control", "peaks": [], "noise": 0.001}
    ]
    rows = []
    for s in samples:
        spec = np.zeros_like(wavelengths)
        for mu, amp, sigma in s["peaks"]:
            spec += gaussian(wavelengths, mu, sigma, amp)
        baseline = 0.0002 * (wavelengths - wavelengths.min())
        noise = np.random.normal(0, s["noise"], size=wavelengths.shape)
        absorbance = spec + baseline + noise
        for wl, a in zip(wavelengths, absorbance):
            rows.append({"sample_id": s["sample_id"], "wavelength_nm": float(wl), "absorbance": float(a)})
    return pd.DataFrame(rows)

def generate_eem():
    excitations = np.arange(250, 401, 5)
    emissions = np.arange(300, 601, 5)
    ex_grid, em_grid = np.meshgrid(excitations, emissions, indexing='xy')
    def g2(ex_grid, em_grid, ex0, em0, sigma_ex, sigma_em, amp):
        return amp * np.exp(-0.5 * (((ex_grid - ex0) / sigma_ex) ** 2 + ((em_grid - em0) / sigma_em) ** 2))
    eem1 = g2(ex_grid, em_grid, 300, 350, 10, 20, 1.0)
    eem2 = g2(ex_grid, em_grid, 320, 420, 8, 25, 0.6)
    eem = eem1 + eem2 + np.random.normal(0, 0.01, size=eem1.shape)
    rows = []
    for i, ex in enumerate(excitations):
        for j, em in enumerate(emissions):
            rows.append({"excitation_nm": int(ex), "emission_nm": int(em), "intensity": float(eem[j, i])})
    return pd.DataFrame(rows)
