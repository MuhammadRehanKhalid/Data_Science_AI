import pandas as pd
import os

def choose_anova_type():
    print("Select ANOVA type:")
    print("1. One-way ANOVA")
    print("2. Two-way ANOVA")
    print("3. Three-way ANOVA")
    print("4. Four-way ANOVA")
    print("5. CRD (Completely Randomized Design)")
    print("6. RCBD (Randomized Complete Block Design)")
    print("7. Split-plot")
    print("8. Split-split plot")
    print("9. Latin Square")
    print("10. Split block")
    print("11. Strip-split")
    print("12. Split-plot Latin Square")
    return input("Enter option number: ").strip()

def choose_file_type():
    print("Select data file type:")
    print("1. CSV")
    print("2. Excel")
    return input("Enter option number: ").strip()

def get_file_path(file_type):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    filetypes = [("CSV Files", "*.csv")] if file_type == "1" else [("Excel Files", "*.xlsx;*.xls")]
    return filedialog.askopenfilename(title="Select Data File", filetypes=filetypes)

def get_output_path(test_name):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    extension = ".xlsx"
    filename = f"{test_name.replace(' ', '_').lower()}_anova_results{extension}"
    filetypes = [("Excel Files", "*.xlsx")]
    file_path = filedialog.asksaveasfilename(
        title="Save Results As",
        defaultextension=extension,
        filetypes=filetypes,
        initialfile=filename
    )
    return file_path, extension

def main():
    anova_choice = choose_anova_type()
    file_type = choose_file_type()

    while True:
        file_path = get_file_path(file_type)
        if file_path:
            break
        print("No file selected.")
        if input("Try again? (y/n): ").strip().lower() != "y":
            return

    try:
        if file_type == "1":
            df = pd.read_csv(file_path)
        else:
            sheet = input("Enter Excel sheet name (leave blank for first sheet): ").strip()
            df = pd.read_excel(file_path, sheet_name=sheet if sheet else 0)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    test_name = {
        "1": "One-way",
        "2": "Two-way",
        "3": "Three-way",
        "4": "Four-way",
        "5": "CRD",
        "6": "RCBD",
        "7": "Split-plot",
        "8": "Split-split",
        "9": "Latin Square",
        "10": "Split-block",
        "11": "Strip-split",
        "12": "Split-plot Latin Square"
    }.get(anova_choice, "anova")

    output_path, extension = get_output_path(test_name)
    if not output_path:
        print("No output file selected. Exiting.")
        return

    try:
        if anova_choice == "1":
            from anova.one_way import one_way_anova
            one_way_anova(df, output_path)

        elif anova_choice == "2":
            from anova.two_way import two_way_anova
            f1, f2 = df.columns[:2]
            two_way_anova(df, f1, f2, output_path)

        elif anova_choice == "3":
            from anova.three_way import three_way_anova
            f1, f2, f3 = df.columns[:3]
            three_way_anova(df, f1, f2, f3, output_path)

        elif anova_choice == "4":
            from anova.four_way import four_way_anova
            f1, f2, f3, f4 = df.columns[:4]
            four_way_anova(df, f1, f2, f3, f4, output_path)

        elif anova_choice == "5":
            from anova.crd import crd_anova
            crd_anova(df, output_path)

        elif anova_choice == "6":
            from anova.rcbd import rcbd_anova
            treatment, block = df.columns[:2]
            rcbd_anova(df, treatment, block, output_path)

        elif anova_choice == "7":
            from anova.split_plot import split_plot_anova
            mainplot, subplot = df.columns[:2]
            split_plot_anova(df, mainplot, subplot, output_path)

        elif anova_choice == "8":
            from anova.split_split_plot import split_split_plot_anova
            mainplot, subplot, subsubplot = df.columns[:3]
            split_split_plot_anova(df, mainplot, subplot, subsubplot, output_path)

        elif anova_choice == "9":
            from anova.latin_square import latin_square_anova
            row, column, treatment = df.columns[:3]
            latin_square_anova(df, row, column, treatment, output_path)

        elif anova_choice == "10":
            from anova.split_block import split_block_anova
            block1, block2, treatment = df.columns[:3]
            split_block_anova(df, block1, block2, treatment, output_path)

        elif anova_choice == "11":
            from anova.strip_split import strip_split_anova
            strip1, strip2, subplot = df.columns[:3]
            strip_split_anova(df, strip1, strip2, subplot, output_path)

        elif anova_choice == "12":
            from anova.split_plot_latin_square import split_plot_latin_square_anova
            row, column, mainplot, subplot = df.columns[:4]
            split_plot_latin_square_anova(df, row, column, mainplot, subplot, output_path)

        else:
            print("Invalid option or not implemented yet.")

        print(f"ANOVA results saved to: {output_path}")

    except Exception as e:
        print(f"Error during analysis: {e}")

if __name__ == "__main__":
    main()
