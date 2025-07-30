import pandas as pd
import os
import sys
import hashlib
import tkinter as tk
from tkinter import filedialog

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

# ==================== ORIGINAL ANOVA TOOL ====================
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

def perform_analysis(anova_choice, df, output_path):
    try:
        test_config = {
            "1": ("one_way", 0),    # Only needs df and output_path
            "2": ("two_way", 2),     # Needs 2 factor columns
            "3": ("three_way", 3),   # Needs 3 factor columns
            "4": ("four_way", 4),    # Needs 4 factor columns
            "5": ("crd", 1),         # Needs 1 treatment column
            "6": ("rcbd", 2),        # Needs treatment + block columns
            "7": ("split_plot", 2),  # Needs mainplot + subplot columns
            "8": ("split_split_plot", 3),  # Needs 3 columns
            "9": ("latin_square", 3),       # Needs row, column, treatment
            "10": ("split_block", 3),       # Needs 3 columns
            "11": ("strip_split", 3),       # Needs 3 columns
            "12": ("split_plot_latin_square", 4)  # Needs 4 columns
        }
        
        module_name, req_columns = test_config.get(anova_choice, (None, 0))
        if not module_name:
            print("Invalid ANOVA type selected.")
            return False
        
        module = __import__(f"anova.{module_name}", fromlist=[f"{module_name}_anova"])
        anova_func = getattr(module, f"{module_name}_anova")
        
        if req_columns == 0:  # One-way ANOVA
            anova_func(df, output_path)
        else:
            columns = list(df.columns[:req_columns])
            anova_func(df, *columns, output_path)
            
        return True
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        return False

def main():
    # Strict license check (no trial period)
    if not validate_license():
        sys.exit(1)
    
    print("\n" + "="*50)
    print("ANOVA Analysis Tool (Licensed Version)")
    print("="*50 + "\n")
    
    # Original workflow
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
    
    if perform_analysis(anova_choice, df, output_path):
        print(f"\n{test_name} ANOVA completed successfully!")
        print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()