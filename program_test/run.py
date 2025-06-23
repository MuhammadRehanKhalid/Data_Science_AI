import pandas as pd
from anova import one_way_anova

def main():
    import tkinter as tk
    from tkinter import filedialog

    # Create and hide the root Tkinter window
    root = tk.Tk()
    root.withdraw()

    # Prompt user to select a CSV file
    file_path = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )

    # If no file selected, exit
    if not file_path:
        print("No file selected.")
        return

    try:
        # Read the CSV file
        df = pd.read_csv(file_path)

        # Perform ANOVA
        f_stat, p_val = one_way_anova(df, group_col='group', value_col='value')

        # Display results
        print(f"F-statistic: {f_stat:.3f}, p-value: {p_val:.3f}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
