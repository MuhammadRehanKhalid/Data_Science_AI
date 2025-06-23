# Two Way ANOVA with CRD (Completely Randomized Design)
from utils.data import load_data

# Load Excel data from the root data folder
df = load_data("sample_input.xlsx")
print(df.head())

# Or, if your file is in a subfolder (e.g., dummy_data)
# df = load_data("sample_input.xlsx", subfolder="dummy_data")
