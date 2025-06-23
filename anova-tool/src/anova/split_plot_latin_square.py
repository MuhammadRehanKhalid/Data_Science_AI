anova_tool/
│
├── data/
│   ├── raw/                  # Raw data files (e.g., CSV, Excel)
│   ├── processed/            # Processed data files
│   └── dummy_data/           # Dummy data for testing
│
├── notebooks/                # Jupyter notebooks for exploratory analysis
│   ├── exploratory_analysis.ipynb
│   └── anova_analysis.ipynb
│
├── src/                      # Source code for the ANOVA tool
│   ├── __init__.py           # Makes src a package
│   ├── anova.py              # Main ANOVA functions
│   ├── utils.py              # Utility functions (e.g., data cleaning, plotting)
│   ├── lsd.py                # Functions for LSD calculations
│   ├── tukey.py              # Functions for Tukey HSD calculations
│   └── anova_results.py       # Functions for exporting results
│
├── tests/                    # Unit tests for the project
│   ├── __init__.py
│   ├── test_anova.py         # Tests for ANOVA functions
│   ├── test_utils.py         # Tests for utility functions
│   └── test_lsd.py           # Tests for LSD functions
│
├── requirements.txt          # List of dependencies
├── README.md                 # Project overview and instructions
└── setup.py                  # Setup script for packaging