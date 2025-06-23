import os
import pandas as pd

def load_data(filename, subfolder=""):
    """
    Loads a file from the data directory.
    Supports CSV and Excel files.
    """
    # Get the project root (assuming src is directly under project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data", subfolder)
    file_path = os.path.join(data_dir, filename)
    if filename.endswith('.csv'):
        return pd.read_csv(file_path)
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file type: " + filename)
