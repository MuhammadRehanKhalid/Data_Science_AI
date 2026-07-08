from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import levene, probplot, shapiro, t
from statsmodels.stats.multicomp import pairwise_tukeyhsd


def significance_stars(p_value):
    if pd.isna(p_value):
        return ""
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    if p_value < 0.1:
        return "."
    return "ns"


def safe_sheet_name(name, suffix=""):
    name = re.sub(r"[\\/*?:\[\]]", "_", str(name))
    max_base_length = max(1, 31 - len(suffix))
    base = name[:max_base_length]
    return f"{base}{suffix}"


def safe_filename(name):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(name)).strip("_")
    return cleaned or "figure"


def get_lsd_letters_cld(means_sorted, lsd):
    group_names = means_sorted["group"].tolist()
    means = means_sorted["Mean"].values
    n = len(means)
    letter_sets = [set() for _ in range(n)]
    current_letter = ord("a")
    for i in range(n):
        used_letters = set()
        for j in range(i):
            if abs(means[i] - means[j]) > lsd:
                used_letters |= letter_sets[j]
        while chr(current_letter) in used_letters:
            current_letter += 1
        letter_sets[i].add(chr(current_letter))
        for j in range(i + 1, n):
            if abs(means[i] - means[j]) <= lsd:
                letter_sets[j].add(chr(current_letter))
    letters = ["".join(sorted(s)) for s in letter_sets]
    return dict(zip(group_names, letters))


def build_output_assets_dir(output_path):
    output_path = Path(output_path)
    assets_dir = output_path.parent / f"{output_path.stem}_assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def _ordered_levels(series):
    return list(pd.Index(series.dropna().astype(str).unique()).sort_values())


def recommend_plots(df_sub, response, factor_cols):
    recommendations = [
        "interaction_plot",
        "group_boxplot",
        "mean_profile_plot",
        "residual_diagnostics",
    ]

    if len(df_sub) >= 20:
        recommendations.append("qq_plot")

    if pd.api.types.is_numeric_dtype(df_sub[response]):
        skewness = df_sub[response].dropna().skew()
        if pd.notna(skewness) and abs(skewness) > 1:
            recommendations.append("histogram")

    return list(dict.fromkeys(recommendations))


def create_histogram_plot(df_sub, response, fig_path):
    values = df_sub[response].dropna()
    if values.empty:
        return None

    plt.figure(figsize=(8, 4.5))
    plt.hist(values, bins=min(20, max(5, len(values) // 2)), edgecolor="black")
    plt.title(f"Histogram: {response}")
    plt.xlabel(response)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    return fig_path


def create_group_boxplot(df_sub, response, group_col, fig_path):
    groups = _ordered_levels(df_sub[group_col])
    data = [df_sub.loc[df_sub[group_col].astype(str) == group, response].dropna().values for group in groups]
    if not data:
        return None

    plt.figure(figsize=(max(8, len(groups) * 0.8), 5))
    plt.boxplot(data, labels=groups, patch_artist=True)
    plt.xticks(rotation=45, ha="right")
    plt.title(f"{response} by {group_col}")
    plt.ylabel(response)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300)
    plt.close()
    return fig_path


def create_interaction_plot(df_sub, response, mainplot, subplot, fig_path):
    main_levels = _ordered_levels(df_sub[mainplot])
    subplot_levels = _ordered_levels(df_sub[subplot])

    plt.figure(figsize=(8.5, 5.5))
    for main_level in main_levels:
        subset = df_sub[df_sub[mainplot].astype(str) == main_level]
        means = []
        for sub_level in subplot_levels:
            values = subset.loc[subset[subplot].astype(str) == sub_level, response].dropna()
            means.append(values.mean() if len(values) else np.nan)
        plt.plot(subplot_levels, means, marker="o", linewidth=2, label=str(main_level))

    plt.title(f"Interaction plot: {response}")
    plt.xlabel(subplot)
    plt.ylabel(response)
    plt.legend(title=mainplot, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    return fig_path


def create_mean_profile_plot(df_sub, response, mainplot, subplot, fig_path):
    pivot = df_sub.pivot_table(index=subplot, columns=mainplot, values=response, aggfunc="mean")
    pivot = pivot.reindex(index=_ordered_levels(df_sub[subplot]))

    plt.figure(figsize=(8.5, 5.5))
    for column in pivot.columns:
        plt.plot(pivot.index.astype(str), pivot[column], marker="o", linewidth=2, label=str(column))

    plt.title(f"Mean profile: {response}")
    plt.xlabel(subplot)
    plt.ylabel(response)
    plt.legend(title=mainplot, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close()
    return fig_path


def create_residual_diagnostics(model, response, fig_path):
    residuals = model.resid.dropna()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].hist(residuals, bins=min(20, max(5, len(residuals) // 2)), edgecolor="black")
    axes[0].set_title("Residual histogram")
    axes[0].set_xlabel("Residual")
    axes[0].set_ylabel("Frequency")

    probplot(residuals, dist="norm", plot=axes[1])
    axes[1].set_title("Q-Q plot")
    fig.suptitle(f"Residual diagnostics: {response}", y=1.02)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def create_correlation_heatmap(df, numeric_cols, fig_path):
    if len(numeric_cols) < 2:
        return None

    corr = df[numeric_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(max(6, len(numeric_cols) * 0.75), max(5, len(numeric_cols) * 0.75)))
    image = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(numeric_cols)))
    ax.set_yticks(range(len(numeric_cols)))
    ax.set_xticklabels(numeric_cols, rotation=45, ha="right")
    ax.set_yticklabels(numeric_cols)
    for row in range(len(numeric_cols)):
        for col in range(len(numeric_cols)):
            ax.text(col, row, f"{corr.iloc[row, col]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Correlation heatmap")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def run_assumption_checks(model, df_sub, group_col, response):
    residuals = model.resid.dropna()
    checks = []

    if len(residuals) >= 3:
        shapiro_stat, shapiro_p = shapiro(residuals)
        checks.append({
            "Check": "Shapiro-Wilk residual normality",
            "Statistic": shapiro_stat,
            "P-value": shapiro_p,
            "Result": "Pass" if shapiro_p >= 0.05 else "Review",
        })
    else:
        checks.append({
            "Check": "Shapiro-Wilk residual normality",
            "Statistic": np.nan,
            "P-value": np.nan,
            "Result": "Insufficient data",
        })

    grouped = [group[response].dropna().values for _, group in df_sub.groupby(group_col)]
    grouped = [values for values in grouped if len(values) >= 2]
    if len(grouped) >= 2:
        levene_stat, levene_p = levene(*grouped, center="median")
        checks.append({
            "Check": "Levene homogeneity of variance",
            "Statistic": levene_stat,
            "P-value": levene_p,
            "Result": "Pass" if levene_p >= 0.05 else "Review",
        })
    else:
        checks.append({
            "Check": "Levene homogeneity of variance",
            "Statistic": np.nan,
            "P-value": np.nan,
            "Result": "Insufficient data",
        })

    return pd.DataFrame(checks)


def run_tukey_posthoc(df_sub, response, group_col):
    cleaned = df_sub[[group_col, response]].dropna()
    if cleaned[group_col].nunique() < 2:
        return pd.DataFrame()

    tukey = pairwise_tukeyhsd(endog=cleaned[response], groups=cleaned[group_col].astype(str), alpha=0.05)
    tukey_table = pd.DataFrame(tukey.summary().data[1:], columns=tukey.summary().data[0])
    return tukey_table


def build_response_summary(df_sub, response, group_col, model, anova_table, lsd, mse_error, df_error):
    means = df_sub.groupby(group_col)[response].agg(["mean", "count"]).reset_index()
    means.columns = ["group", "Mean", "n"]
    means = means.sort_values("Mean", ascending=False).reset_index(drop=True)
    letters_dict = get_lsd_letters_cld(means, lsd)
    means["Letter"] = means["group"].map(letters_dict)

    alpha = 0.05
    t_critical = t.ppf(1 - alpha / 2, df_error)
    summary = pd.DataFrame({
        "Metric": ["alpha", "t_critical", "df_error", "mse_error", "lsd"],
        "Value": [alpha, t_critical, df_error, mse_error, lsd],
    })

    return summary, means
