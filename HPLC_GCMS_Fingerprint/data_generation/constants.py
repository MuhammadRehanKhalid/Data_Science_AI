"""
Shared constants for HPLC / GC-MS dummy-data generation.
All downstream modules import from here so definitions stay in one place.
"""
import numpy as np

# ---------------------------------------------------------------------------
# Biological entities
# ---------------------------------------------------------------------------
SPECIES: list[str] = [
    "Spirulina platensis",
    "Chlorella vulgaris",
    "Gracilaria gracilis",
    "Sargassum muticum",
    "Nostoc commune",
    "Dunaliella salina",
]

PHYLA: dict[str, str] = {
    "Spirulina platensis": "Cyanobacteria",
    "Chlorella vulgaris":  "Chlorophyta",
    "Gracilaria gracilis": "Rhodophyta",
    "Sargassum muticum":   "Phaeophyceae",
    "Nostoc commune":      "Cyanobacteria",
    "Dunaliella salina":   "Chlorophyta",
}

# Higher baseline → richer phenolic/antioxidant content in the species
SPECIES_BASELINE: dict[str, float] = {
    "Spirulina platensis": 0.65,
    "Chlorella vulgaris":  0.70,
    "Gracilaria gracilis": 0.82,
    "Sargassum muticum":   0.90,
    "Nostoc commune":      0.60,
    "Dunaliella salina":   0.75,
}

# Phylum index for integer encoding (sorted for reproducibility)
PHYLUM_LIST: list[str] = sorted(set(PHYLA.values()))
SPECIES_LIST: list[str] = SPECIES  # ordered list for label encoding

# ---------------------------------------------------------------------------
# Solvents & their physico-chemical properties
# ---------------------------------------------------------------------------
SOLVENTS: list[str] = [
    "Water",
    "MeOH_70",
    "EtOH_70",
    "EtOAc",
    "Acetone_100",
    "MeCN_50",
]

SOLVENT_FULL_NAMES: dict[str, str] = {
    "Water":        "Water",
    "MeOH_70":      "70% Methanol / 30% Water",
    "EtOH_70":      "70% Ethanol / 30% Water",
    "EtOAc":        "Ethyl Acetate",
    "Acetone_100":  "100% Acetone",
    "MeCN_50":      "50% Acetonitrile / 50% Water",
}

SOLVENT_PROPS: dict[str, dict] = {
    "Water":        {"polarity_index": 10.2, "dielectric_constant": 80.1, "is_protic": 1},
    "MeOH_70":      {"polarity_index":  8.1, "dielectric_constant": 55.0, "is_protic": 1},
    "EtOH_70":      {"polarity_index":  7.5, "dielectric_constant": 45.0, "is_protic": 1},
    "EtOAc":        {"polarity_index":  4.4, "dielectric_constant":  6.0, "is_protic": 0},
    "Acetone_100":  {"polarity_index":  5.1, "dielectric_constant": 20.7, "is_protic": 0},
    "MeCN_50":      {"polarity_index":  5.8, "dielectric_constant": 37.5, "is_protic": 0},
}

# ---------------------------------------------------------------------------
# Assays
# ---------------------------------------------------------------------------
ASSAYS: list[str] = ["DPPH", "ABTS", "FRAP"]

# Per-assay sensitivity to solvent polarity (higher → more polar solvents give higher readings)
ASSAY_POLARITY_WEIGHT: dict[str, float] = {
    "DPPH": 0.55,
    "ABTS": 0.60,
    "FRAP": 0.65,
}
ASSAY_BASE_INTERCEPT: dict[str, float] = {
    "DPPH": 0.38,
    "ABTS": 0.33,
    "FRAP": 0.28,
}

# ---------------------------------------------------------------------------
# HPLC peak layout
# ---------------------------------------------------------------------------
N_HPLC_PEAKS: int = 50
RT_MIN: float = 0.5   # minutes
RT_MAX: float = 30.0  # minutes

_rt_rng = np.random.default_rng(seed=0)
HPLC_RT_CENTERS: np.ndarray = np.sort(
    _rt_rng.uniform(RT_MIN, RT_MAX, N_HPLC_PEAKS)
)

# ---------------------------------------------------------------------------
# GC-MS m/z layout
# ---------------------------------------------------------------------------
N_MZ_BINS: int = 80
MZ_MIN: float = 50.0   # Da
MZ_MAX: float = 500.0  # Da

_mz_rng = np.random.default_rng(seed=1)
MZ_BIN_CENTERS: np.ndarray = np.sort(
    _mz_rng.uniform(MZ_MIN, MZ_MAX, N_MZ_BINS)
)
