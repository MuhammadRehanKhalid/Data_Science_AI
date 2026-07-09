from pathlib import Path

import hashlib
import os
import sys

import pandas as pd
import tkinter as tk
from tkinter import filedialog

from anova.advanced_tools import normalize_posthoc_method, set_posthoc_method, suggest_posthoc_test
from anova.dummy_data import DESIGN_SPECS, generate_and_save_dummy_dataset

# ==================== LICENSE SYSTEM ====================
# Generate your hash by running: hashlib.sha256("your_key".encode()).hexdigest()
LICENSE_HASH = hashlib.sha256("rehan@12345".encode()).hexdigest()  # Example: "password"

def validate_license():
    """Check for valid license key through environment variable or file"""
    # Method 1: Environment variable
    env_key = os.getenv("ANOVA_LICENSE_KEY")
    if env_key and hashlib.sha256(env_key.encode()).hexdigest() == LICENSE_HASH:
        return True
    
    # Method 2: License file
    license_file = os.path.join(os.path.dirname(__file__), "anova.license")
    if os.path.exists(license_file):
        with open(license_file, "r") as f:
            file_key = f.read().strip()
            if hashlib.sha256(file_key.encode()).hexdigest() == LICENSE_HASH:
                return True
    
    # Prompt for license key
    print("\nANOVA Tool - License Required")
    print("-----------------------------")
    user_key = input("Enter license key: ").strip()
    
    if hashlib.sha256(user_key.encode()).hexdigest() == LICENSE_HASH:
        with open(license_file, "w") as f:
            f.write(user_key)
        print("License activated successfully!")
        return True
    
    print("Invalid license key. Exiting.")
    return False

TEST_CONFIG = {
    "1": ("one_way", 1),
    "2": ("two_way", 2),
    "3": ("three_way", 3),
    "4": ("four_way", 4),
    "5": ("crd", 1),
    "6": ("rcbd", 2),
    "7": ("split_plot", 2),
    "8": ("split_split_plot", 3),
    "9": ("latin_square", 3),
    "10": ("split_block", 3),
    "11": ("strip_split", 3),
    "12": ("split_plot_latin_square", 4),
}


def choose_operation():
    print("\nSelect an option:")
    print("1. Analyze data")
    print("2. Generate dummy data")
    print("3. Exit")
    while True:
        choice = input("Enter option number (1-3): ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("Invalid input. Please enter 1, 2, or 3.")


def choose_anova_type():
    print("\nSelect ANOVA type:")
    options = [
        "1. One-way ANOVA",
        "2. Two-way ANOVA",
        "3. Three-way ANOVA",
        "4. Four-way ANOVA",
        "5. CRD (Completely Randomized Design)",
        "6. RCBD (Randomized Complete Block Design)",
        "7. Split-plot",
        "8. Split-split plot",
        "9. Latin Square",
        "10. Split block",
        "11. Strip-split",
        "12. Split-plot Latin Square"
    ]
    print("\n".join(options))
    while True:
        choice = input("Enter option number (1-12): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= 12:
            return choice
        print("Invalid input. Please enter a number between 1 and 12.")

def choose_file_type():
    print("\nSelect data file type:")
    print("1. CSV")
    print("2. Excel")
    while True:
        choice = input("Enter option number (1-2): ").strip()
        if choice in ("1", "2"):
            return choice
        print("Invalid input. Please enter 1 or 2.")


def choose_dummy_rows_per_cell():
    while True:
        value = input("Enter rows per cell for dummy data [default 4]: ").strip()
        if value == "":
            return 4
        if value.isdigit() and int(value) > 0:
            return int(value)
        print("Invalid input. Please enter a positive integer.")


def choose_posthoc_method(recommendation):
    print("\nPost hoc recommendation:")
    print(f"- Suggested method: {recommendation['method']}")
    print(f"- Reason: {recommendation['reason']}")
    print("\nSelect post hoc test:")
    options = [
        "1. Use recommended",
        "2. Tukey HSD",
        "3. Tukey-Kramer",
        "4. Games-Howell",
        "5. Duncan",
        "6. Student-Newman-Keuls",
        "7. Holm",
        "8. Bonferroni",
        "9. Sidak",
        "10. LSD",
        "11. Scheffe",
    ]
    print("\n".join(options))
    mapping = {
        "1": recommendation["method"],
        "2": "Tukey HSD",
        "3": "Tukey-Kramer",
        "4": "Games-Howell",
        "5": "Duncan",
        "6": "Student-Newman-Keuls",
        "7": "Holm",
        "8": "Bonferroni",
        "9": "Sidak",
        "10": "LSD",
        "11": "Scheffe",
    }
    while True:
        choice = input("Enter option number (1-11): ").strip()
        if choice in mapping:
            selected = normalize_posthoc_method(mapping[choice])
            print(f"Using post hoc method: {selected}")
            return selected
        print("Invalid input. Please enter a number between 1 and 11.")


def get_booklet_path():
    return Path(__file__).resolve().parents[1] / "docs" / "ANOVA_Booklet.md"

def get_file_path(file_type):
    root = tk.Tk()
    root.withdraw()
    filetypes = [("CSV Files", "*.csv")] if file_type == "1" else [
        ("Excel Files", "*.xlsx;*.xls"),
        ("All files", "*.*")
    ]
    return filedialog.askopenfilename(
        title="Select Data File",
        filetypes=filetypes
    )

def get_output_path(test_name):
    root = tk.Tk()
    root.withdraw()
    extension = ".xlsx"
    filename = f"{test_name.replace(' ', '_').lower()}_anova_results{extension}"
    return filedialog.asksaveasfilename(
        title="Save Results As",
        defaultextension=extension,
        filetypes=[("Excel Files", "*.xlsx")],
        initialfile=filename
    )


def get_dummy_output_path(design_name, file_type):
    root = tk.Tk()
    root.withdraw()
    extension = ".csv" if file_type == "1" else ".xlsx"
    filename = f"dummy_{design_name.replace(' ', '_').lower()}{extension}"
    filetypes = [("CSV Files", "*.csv")] if file_type == "1" else [("Excel Files", "*.xlsx")]
    return filedialog.asksaveasfilename(
        title="Save Dummy Data As",
        defaultextension=extension,
        filetypes=filetypes,
        initialfile=filename,
    )

def load_data_file(file_type, file_path):
    try:
        if file_type == "1":
            return pd.read_csv(file_path)
        else:
            sheet = input("Enter Excel sheet name (leave blank for first sheet): ").strip()
            return pd.read_excel(file_path, sheet_name=sheet if sheet else 0)
    except Exception as e:
        print(f"\nError loading file: {str(e)}")
        return None


def build_posthoc_recommendation(anova_choice, df):
    module_name, req_columns = TEST_CONFIG.get(anova_choice, (None, 0))
    if not module_name or len(df.columns) <= req_columns:
        return {
            "method": "Recommended",
            "reason": "The dataset does not contain enough columns to infer a post hoc strategy.",
        }

    factor_cols = list(df.columns[:req_columns])
    response_cols = [col for col in df.columns[req_columns:] if pd.api.types.is_numeric_dtype(df[col])]
    if not response_cols:
        return {
            "method": "Recommended",
            "reason": "No numeric response column was found for post hoc recommendation.",
        }

    response = response_cols[0]
    df_sub = df[factor_cols + [response]].dropna().copy()
    if req_columns == 1:
        group_col = factor_cols[0]
        df_sub[group_col] = df_sub[group_col].astype(str)
    else:
        group_col = "group"
        df_sub[group_col] = df_sub[factor_cols].astype(str).agg("_".join, axis=1)

    recommendation = suggest_posthoc_test(df_sub, group_col, response)
    return recommendation


def perform_analysis(anova_choice, df, output_path, posthoc_method):
    try:
        module_name, req_columns = TEST_CONFIG.get(anova_choice, (None, 0))
        if not module_name:
            print("Invalid ANOVA type selected.")
            return False
        
        set_posthoc_method(posthoc_method)
        module = __import__(f"anova.{module_name}", fromlist=[f"{module_name}_anova"])
        anova_func = getattr(module, f"{module_name}_anova")
        
        if req_columns == 1 and anova_choice == "1":
            anova_func(df, output_path)
        else:
            columns = list(df.columns[:req_columns])
            anova_func(df, *columns, output_path)
            
        return True
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        return False


def generate_dummy_data_workflow():
    anova_choice = choose_anova_type()
    file_type = choose_file_type()
    rows_per_cell = choose_dummy_rows_per_cell()
    output_path = get_dummy_output_path(TEST_CONFIG[anova_choice][0].replace("_", " ").title(), file_type)

    if not output_path:
        print("No output file selected. Exiting.")
        return

    df, saved_path = generate_and_save_dummy_dataset(anova_choice, output_path, rows_per_cell=rows_per_cell)
    print(f"\nDummy data generated successfully for: {TEST_CONFIG[anova_choice][0].replace('_', ' ').title()}")
    print(f"Rows: {len(df)}")
    print(f"Saved to: {saved_path}")

def main():
    # Strict license check (no trial period)
    if not validate_license():
        sys.exit(1)
    
    print("\n" + "="*50)
    print("ANOVA Analysis Tool (Licensed Version)")
    print("="*50 + "\n")

    booklet_path = get_booklet_path()
    print(f"Booklet: {booklet_path}")

    operation = choose_operation()
    if operation == "3":
        return

    if operation == "2":
        generate_dummy_data_workflow()
        return

    anova_choice = choose_anova_type()
    file_type = choose_file_type()

    file_path = None
    while not file_path:
        file_path = get_file_path(file_type)
        if not file_path:
            if input("No file selected. Try again? (y/n): ").strip().lower() != 'y':
                return

    df = load_data_file(file_type, file_path)
    if df is None:
        return

    recommendation = build_posthoc_recommendation(anova_choice, df)
    posthoc_method = choose_posthoc_method(recommendation)

    test_name = {
        "1": "One-way", "2": "Two-way", "3": "Three-way", "4": "Four-way",
        "5": "CRD", "6": "RCBD", "7": "Split-plot", "8": "Split-split",
        "9": "Latin Square", "10": "Split-block", "11": "Strip-split",
        "12": "Split-plot Latin Square"
    }.get(anova_choice, "ANOVA")

    output_path = get_output_path(test_name)
    if not output_path:
        print("No output file selected. Exiting.")
        return

    if perform_analysis(anova_choice, df, output_path, posthoc_method):
        print(f"\n{test_name} ANOVA completed successfully!")
        print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()