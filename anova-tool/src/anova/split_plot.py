import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
from scipy.stats import t
import re

def significance_stars(p):
    if p < 0.001: return '***'
    elif p < 0.01: return '**'
    elif p < 0.05: return '*'
    elif p < 0.1: return '.'
    else: return 'ns'

def get_lsd_letters_cld(means_sorted, lsd):
    group_names = means_sorted['group'].tolist()
    means = means_sorted['Mean'].values
    n = len(means)
    letter_sets = [set() for _ in range(n)]
    current_letter = ord('a')
    for i in range(n):
        used_letters = set()
        for j in range(i):
            if abs(means[i] - means[j]) > lsd:
                used_letters |= letter_sets[j]
        while chr(current_letter) in used_letters:
            current_letter += 1
        letter_sets[i].add(chr(current_letter))
        for j in range(i+1, n):
            if abs(means[i] - means[j]) <= lsd:
                letter_sets[j].add(chr(current_letter))
    letters = [''.join(sorted(s)) for s in letter_sets]
    return dict(zip(group_names, letters))

def safe_sheet_name(name, suffix=""):
    name = re.sub(r'[\\/*?:\[\]]', '_', str(name))
    base = name[:25]
    return f"{base}{suffix}"

def split_plot_anova(df, mainplot, subplot, output_path):
    response_cols = df.columns.difference([mainplot, subplot]).tolist()

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for response in response_cols:
            df_sub = df[[mainplot, subplot, response]].dropna()
            df_sub['group'] = df_sub[[mainplot, subplot]].astype(str).agg('_'.join, axis=1)

            formula = f'{response} ~ C({mainplot}) * C({subplot})'
            model = ols(formula, data=df_sub).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)
            anova_table['P-value'] = anova_table['PR(>F)']
            anova_table['Signif.'] = anova_table['PR(>F)'].apply(significance_stars)

            df_error = anova_table.loc['Residual', 'df']
            mse_error = anova_table.loc['Residual', 'sum_sq'] / df_error

            means = df_sub.groupby('group')[response].agg(['mean', 'count']).reset_index()
            means.columns = ['group', 'Mean', 'n']
            means = means.sort_values('Mean', ascending=False).reset_index(drop=True)

            n_eff = means['n'].min()
            alpha = 0.05
            t_critical = t.ppf(1 - alpha / 2, df_error)
            lsd = t_critical * np.sqrt(2 * mse_error / n_eff)

            letters_dict = get_lsd_letters_cld(means, lsd)
            means['Letter'] = means['group'].map(letters_dict)

            safe_name = safe_sheet_name(response)
            anova_table.to_excel(writer, sheet_name=f'{safe_name}_ANOVA')
            pd.DataFrame({
                'LSD_value': [lsd],
                'alpha': [alpha],
                't_critical': [t_critical],
                'df_error': [df_error],
                'mse_error': [mse_error]
            }).to_excel(writer, sheet_name=f'{safe_name}_LSD', index=False)
            means.to_excel(writer, sheet_name=f'{safe_name}_Means', index=False)

    print("✅ Split-Plot ANOVA results saved to Excel.")
