# src/config.py

RANDOM_STATE = None  # None = random seed each run (different data each time)
N_SAMPLES = 10000   # Much larger dataset
TEST_SIZE = 0.2

TARGET_COLUMNS = [
	"ORAC",
	"FRAP",
	"DPPH",
	"ABTS",
	"TPC"
]

FIGURE_DIR = "figures"
MODEL_DIR = "models"
DATA_DIR = "data"
