import pandas as pd
from anova.one_way import one_way_anova

def main():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )

    if not file_path:
        print("No file selected.")
        return

    try:
        df = pd.read_csv(file_path)
        f_stat, p_val = one_way_anova(df, group_col='group', value_col='value')
        print(f"F-statistic: {f_stat:.3f}, p-value: {p_val:.3f}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()