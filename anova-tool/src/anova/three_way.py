from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import t
from statsmodels.formula.api import ols

from .advanced_tools import (
    build_output_assets_dir,
    create_correlation_heatmap,
    create_group_boxplot,
    create_histogram_plot,
    create_interaction_plot,
    create_residual_diagnostics,
    build_posthoc_guide_table,
    get_lsd_letters_cld,
    recommend_plots,
    run_assumption_checks,
    run_tukey_posthoc,
    safe_filename,
    safe_sheet_name,
    significance_stars,
)


def three_way_anova(df, factor1, factor2, factor3, output_path):
    response_cols = df.columns.difference([factor1, factor2, factor3]).tolist()
    numeric_responses = [col for col in response_cols if pd.api.types.is_numeric_dtype(df[col])]
    plot_index_rows = []
    run_rows = []
    assets_dir = build_output_assets_dir(output_path)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        if len(numeric_responses) >= 2:
            corr_path = assets_dir / 'correlation_heatmap.png'
            corr_matrix = df[numeric_responses].corr(numeric_only=True)
            create_correlation_heatmap(df, numeric_responses, corr_path)
            corr_matrix.to_excel(writer, sheet_name='Correlation_Matrix')
            plot_index_rows.append({'Response': 'all_numeric_responses', 'Plot': 'correlation_heatmap', 'File': str(corr_path), 'Status': 'saved'})

        for response in response_cols:
            df_sub = df[[factor1, factor2, factor3, response]].dropna().copy()
            if df_sub.empty:
                continue

            df_sub['group'] = df_sub[[factor1, factor2, factor3]].astype(str).agg('_'.join, axis=1)

            formula = f'{response} ~ C({factor1})*C({factor2})*C({factor3})'
            model = ols(formula, data=df_sub).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)
            anova_table['P-value'] = anova_table['PR(>F)']
            anova_table['Signif.'] = anova_table['PR(>F)'].apply(significance_stars)

            df_error = anova_table.loc['Residual', 'df'] if 'Residual' in anova_table.index else anova_table.iloc[-1]['df']
            mse_error = anova_table.loc['Residual', 'sum_sq'] / df_error if 'Residual' in anova_table.index and df_error else anova_table.iloc[-1]['sum_sq'] / anova_table.iloc[-1]['df']

            means = df_sub.groupby('group')[response].agg(['mean', 'count']).reset_index()
            means.columns = ['group', 'Mean', 'n']
            means = means.sort_values('Mean', ascending=False).reset_index(drop=True)

            n_eff = means['n'].min()
            alpha = 0.05
            t_critical = t.ppf(1 - alpha / 2, df_error) if pd.notna(df_error) and df_error > 0 else np.nan
            lsd = t_critical * np.sqrt(2 * mse_error / n_eff) if pd.notna(t_critical) and pd.notna(mse_error) and n_eff > 0 else np.nan

            letters_dict = get_lsd_letters_cld(means, lsd)
            means['Letter'] = means['group'].map(letters_dict)

            assumptions = run_assumption_checks(model, df_sub, 'group', response)
            posthoc = run_tukey_posthoc(df_sub, response, 'group')
            plot_guide = pd.DataFrame({'Recommended Plot': recommend_plots(df_sub, response, [factor1, factor2, factor3])})
            response_summary = pd.DataFrame({'Metric': ['response', 'groups', 'mean_min', 'mean_max', 'anova_pvalue', 'residual_normality', 'variance_homogeneity'], 'Value': [response, means['group'].nunique(), means['Mean'].min() if not means.empty else np.nan, means['Mean'].max() if not means.empty else np.nan, anova_table['P-value'].iloc[0] if len(anova_table) else np.nan, assumptions.loc[assumptions['Check'] == 'Shapiro-Wilk residual normality', 'Result'].iloc[0], assumptions.loc[assumptions['Check'] == 'Levene homogeneity of variance', 'Result'].iloc[0]]})

            safe_name = safe_sheet_name(response)
            anova_table.to_excel(writer, sheet_name=f'{safe_name}_ANOVA')
            pd.DataFrame({'Metric': ['alpha', 't_critical', 'df_error', 'mse_error', 'lsd'], 'Value': [alpha, t_critical, df_error, mse_error, lsd]}).to_excel(writer, sheet_name=f'{safe_name}_LSD', index=False)
            means.to_excel(writer, sheet_name=f'{safe_name}_Means', index=False)
            assumptions.to_excel(writer, sheet_name=f'{safe_name}_Checks', index=False)
            response_summary.to_excel(writer, sheet_name=f'{safe_name}_Summary', index=False)
            plot_guide.to_excel(writer, sheet_name=f'{safe_name}_Plots', index=False)
            if not posthoc.empty:
                posthoc.to_excel(writer, sheet_name=f'{safe_name}_Posthoc', index=False)
                build_posthoc_guide_table(posthoc).to_excel(writer, sheet_name=f'{safe_name}_Posthoc_Guide', index=False)

            response_slug = safe_filename(response)
            boxplot_path = assets_dir / f'{response_slug}_boxplot.png'
            interaction_path = assets_dir / f'{response_slug}_interaction.png'
            diagnostics_path = assets_dir / f'{response_slug}_diagnostics.png'
            histogram_path = assets_dir / f'{response_slug}_histogram.png'
            saved_plots = [
                ('group_boxplot', create_group_boxplot(df_sub, response, 'group', boxplot_path)),
                ('interaction_plot', create_interaction_plot(df_sub, response, factor1, factor2, interaction_path)),
                ('residual_diagnostics', create_residual_diagnostics(model, response, diagnostics_path)),
            ]
            if 'histogram' in plot_guide['Recommended Plot'].tolist():
                saved_plots.append(('histogram', create_histogram_plot(df_sub, response, histogram_path)))

            for plot_name, plot_path in saved_plots:
                if plot_path:
                    plot_index_rows.append({'Response': response, 'Plot': plot_name, 'File': str(plot_path), 'Status': 'saved'})

            run_rows.append({'Response': response, 'ANOVA_Pvalue': anova_table['P-value'].iloc[0] if len(anova_table) else np.nan, 'Residual_Normality': assumptions.loc[assumptions['Check'] == 'Shapiro-Wilk residual normality', 'Result'].iloc[0], 'Variance_Homogeneity': assumptions.loc[assumptions['Check'] == 'Levene homogeneity of variance', 'Result'].iloc[0], 'LSD': lsd})

        if plot_index_rows:
            pd.DataFrame(plot_index_rows).to_excel(writer, sheet_name='Plot_Index', index=False)
        if run_rows:
            pd.DataFrame(run_rows).to_excel(writer, sheet_name='Run_Summary', index=False)

    print(f'Exported all ANOVA, LSD, and advanced outputs for all responses: {Path(output_path)}')
    print(f'Figures saved in: {assets_dir}')

# Example use
if __name__ == "__main__":
    file_path = "C:\\Users\\mirza\\OneDrive\\Desktop\\Copy of Mungbean_Excel_sheet(1).xlsx"
    sheet_name = "Sheet3"
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    factor1, factor2, factor3 = df.columns[:3]
    output_path = "three_way_anova_results.xlsx"
    three_way_anova(df, factor1, factor2, factor3, output_path)
