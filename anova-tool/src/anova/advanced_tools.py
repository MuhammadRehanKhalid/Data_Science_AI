from pathlib import Path
from itertools import combinations
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import f, levene, probplot, shapiro, t, ttest_ind
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests

try:
    from statsmodels.stats.libqsturng import psturng, qsturng
except Exception:  # pragma: no cover - fallback if statsmodels internals move
    psturng = None
    qsturng = None


POSTHOC_METHOD = "Recommended"


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


def set_posthoc_method(method):
    global POSTHOC_METHOD
    POSTHOC_METHOD = normalize_posthoc_method(method)


def normalize_posthoc_method(method):
    if method is None:
        return "Recommended"

    normalized = str(method).strip().lower()
    mapping = {
        "recommended": "Recommended",
        "auto": "Recommended",
        "tukey": "Tukey HSD",
        "tukey hsd": "Tukey HSD",
        "tukey-kramer": "Tukey-Kramer",
        "tukey kramer": "Tukey-Kramer",
        "tukeykramer": "Tukey-Kramer",
        "bonferroni": "Bonferroni",
        "holm": "Holm",
        "sidak": "Sidak",
        "lsd": "LSD",
        "games-howell": "Games-Howell",
        "games howell": "Games-Howell",
        "gameshowell": "Games-Howell",
        "scheffe": "Scheffe",
        "scheffé": "Scheffe",
        "duncan": "Duncan",
        "student-newman-keuls": "Student-Newman-Keuls",
        "student newman keuls": "Student-Newman-Keuls",
        "snk": "Student-Newman-Keuls",
    }
    return mapping.get(normalized, method)


def suggest_posthoc_test(df_sub, group_col, response):
    cleaned = df_sub[[group_col, response]].dropna().copy()
    group_sizes = cleaned.groupby(group_col).size()
    n_groups = int(group_sizes.shape[0])
    balanced = group_sizes.nunique() == 1 if n_groups else False

    grouped_values = [values[response].dropna().values for _, values in cleaned.groupby(group_col)]
    grouped_values = [values for values in grouped_values if len(values) >= 2]

    if len(grouped_values) >= 2:
        levene_stat, levene_p = levene(*grouped_values, center="median")
    else:
        levene_p = np.nan

    if n_groups <= 2:
        method = "LSD"
        reason = "Only two groups are present, so a simple pairwise comparison is sufficient."
    elif pd.notna(levene_p) and levene_p >= 0.05 and balanced:
        method = "Tukey HSD"
        reason = "Group sizes are balanced and variances look similar, so Tukey HSD is a strong all-pairs choice."
    elif pd.notna(levene_p) and levene_p < 0.05:
        method = "Games-Howell"
        reason = "Variances look unequal, so Games-Howell is more appropriate because it does not assume equal variances."
    elif not balanced:
        method = "Tukey-Kramer"
        reason = "Group sizes are unbalanced but variances appear similar, so Tukey-Kramer is a better default than plain Tukey HSD."
    else:
        method = "Bonferroni"
        reason = "The design is fairly simple, but Bonferroni is a conservative fallback when a stricter adjustment is preferred."

    return {
        "method": method,
        "reason": reason,
        "balanced": balanced,
        "levene_pvalue": levene_p,
        "groups": n_groups,
    }


def _pairwise_ttest_table(df_sub, response, group_col, correction_method, equal_var):
    cleaned = df_sub[[group_col, response]].dropna().copy()
    groups = list(cleaned[group_col].astype(str).unique())
    rows = []

    for group_a, group_b in combinations(groups, 2):
        values_a = cleaned.loc[cleaned[group_col].astype(str) == group_a, response].dropna().values
        values_b = cleaned.loc[cleaned[group_col].astype(str) == group_b, response].dropna().values
        stat, p_value = ttest_ind(values_a, values_b, equal_var=equal_var, nan_policy="omit")
        rows.append({
            "Group1": group_a,
            "Group2": group_b,
            "Statistic": stat,
            "P-raw": p_value,
        })

    if not rows:
        return pd.DataFrame()

    table = pd.DataFrame(rows)
    if correction_method == "none":
        table["P-adj"] = table["P-raw"]
        table["Reject"] = table["P-raw"] < 0.05
    else:
        reject, p_adj, _, _ = multipletests(table["P-raw"].values, alpha=0.05, method=correction_method)
        table["P-adj"] = p_adj
        table["Reject"] = reject

    return table


def _pairwise_range_table(df_sub, response, group_col, range_correction, alpha=0.05):
    cleaned = df_sub[[group_col, response]].dropna().copy()
    group_stats = cleaned.groupby(group_col)[response].agg(["mean", "var", "count"]).reset_index()
    if len(group_stats) < 2 or qsturng is None or psturng is None:
        return pd.DataFrame()

    group_stats = group_stats.sort_values("mean", ascending=False).reset_index(drop=True)
    total_groups = len(group_stats)
    rows = []

    for left_index, left in group_stats.iterrows():
        for right_index in range(left_index + 1, total_groups):
            right = group_stats.iloc[right_index]
            range_size = right_index - left_index + 1
            left_term = left["var"] / left["count"] if left["count"] > 0 else np.nan
            right_term = right["var"] / right["count"] if right["count"] > 0 else np.nan
            se = np.sqrt(0.5 * (left_term + right_term))
            if not np.isfinite(se) or se == 0:
                continue

            q_stat = abs(left["mean"] - right["mean"]) / se
            if range_correction == "snk":
                critical_alpha = alpha
            elif range_correction == "duncan":
                critical_alpha = 1 - (1 - alpha) ** max(1, range_size - 1)
            else:
                critical_alpha = alpha

            q_crit = qsturng(1 - critical_alpha, range_size, max(1, len(cleaned) - total_groups))
            p_value = 1 - psturng(q_stat, range_size, max(1, len(cleaned) - total_groups))
            rows.append({
                "Group1": str(left[group_col]),
                "Group2": str(right[group_col]),
                "Statistic": q_stat,
                "Range": range_size,
                "Critical": q_crit,
                "P-raw": p_value,
                "P-adj": p_value,
                "Reject": bool(q_stat > q_crit),
            })

    return pd.DataFrame(rows)


def _pairwise_tukey_kramer_table(df_sub, response, group_col):
    cleaned = df_sub[[group_col, response]].dropna().copy()
    group_stats = cleaned.groupby(group_col)[response].agg(["mean", "var", "count"]).reset_index()
    if len(group_stats) < 2 or qsturng is None or psturng is None:
        return pd.DataFrame()

    df_error = len(cleaned) - len(group_stats)
    if df_error <= 0:
        return pd.DataFrame()

    rows = []
    for _, left in group_stats.iterrows():
        for _, right in group_stats.iterrows():
            if str(left[group_col]) >= str(right[group_col]):
                continue
            mean_diff = abs(left[response] - right[response])
            left_term = left["var"] / left["count"] if left["count"] > 0 else np.nan
            right_term = right["var"] / right["count"] if right["count"] > 0 else np.nan
            se = np.sqrt(0.5 * (left_term + right_term))
            if not np.isfinite(se) or se == 0:
                continue

            q_stat = mean_diff / se
            q_crit = qsturng(0.95, len(group_stats), df_error)
            p_value = 1 - psturng(q_stat, len(group_stats), df_error)
            rows.append({
                "Group1": str(left[group_col]),
                "Group2": str(right[group_col]),
                "Statistic": q_stat,
                "df": df_error,
                "Critical": q_crit,
                "P-raw": p_value,
                "P-adj": p_value,
                "Reject": bool(q_stat > q_crit),
            })

    return pd.DataFrame(rows)


def _pairwise_games_howell_table(df_sub, response, group_col):
    cleaned = df_sub[[group_col, response]].dropna().copy()
    group_stats = cleaned.groupby(group_col)[response].agg(["mean", "var", "count"]).reset_index()
    if len(group_stats) < 2 or qsturng is None or psturng is None:
        return pd.DataFrame()

    rows = []
    group_names = group_stats[group_col].astype(str).tolist()
    total_groups = len(group_names)

    for _, left in group_stats.iterrows():
        for _, right in group_stats.iterrows():
            if str(left[group_col]) >= str(right[group_col]):
                continue
            mean_diff = abs(left[response] - right[response])
            left_term = left["var"] / left["count"] if left["count"] > 0 else np.nan
            right_term = right["var"] / right["count"] if right["count"] > 0 else np.nan
            se = np.sqrt((left_term + right_term) / 2)
            if not np.isfinite(se) or se == 0:
                continue

            q_stat = mean_diff / se
            denominator = 0.0
            if left["count"] > 1:
                denominator += (left_term ** 2) / (left["count"] - 1)
            if right["count"] > 1:
                denominator += (right_term ** 2) / (right["count"] - 1)
            if denominator <= 0:
                continue

            df_welch = ((left_term + right_term) ** 2) / denominator
            q_crit = qsturng(0.95, total_groups, df_welch)
            p_value = 1 - psturng(q_stat, total_groups, df_welch)
            rows.append({
                "Group1": str(left[group_col]),
                "Group2": str(right[group_col]),
                "Statistic": q_stat,
                "df": df_welch,
                "P-raw": p_value,
                "P-adj": p_value,
                "Reject": bool(q_stat > q_crit),
            })

    return pd.DataFrame(rows)


def _pairwise_scheffe_table(df_sub, response, group_col):
    cleaned = df_sub[[group_col, response]].dropna().copy()
    group_stats = cleaned.groupby(group_col)[response].agg(["mean", "var", "count"]).reset_index()
    if len(group_stats) < 2:
        return pd.DataFrame()

    total_groups = len(group_stats)
    result_rows = []
    pooled_mse = cleaned.groupby(group_col)[response].var().mean()
    if not np.isfinite(pooled_mse) or pooled_mse <= 0:
        pooled_mse = cleaned[response].var(ddof=1)

    df_error = len(cleaned) - total_groups
    if df_error <= 0 or not np.isfinite(pooled_mse) or pooled_mse <= 0:
        return pd.DataFrame()

    f_crit = f.ppf(0.95, total_groups - 1, df_error)
    for _, left in group_stats.iterrows():
        for _, right in group_stats.iterrows():
            if str(left[group_col]) >= str(right[group_col]):
                continue
            mean_diff = abs(left[response] - right[response])
            se_term = pooled_mse * (1 / left["count"] + 1 / right["count"])
            if se_term <= 0:
                continue
            f_stat = (mean_diff ** 2) / (se_term * max(1, total_groups - 1))
            p_value = 1 - f.cdf(f_stat, total_groups - 1, df_error)
            result_rows.append({
                "Group1": str(left[group_col]),
                "Group2": str(right[group_col]),
                "Statistic": f_stat,
                "df": df_error,
                "P-raw": p_value,
                "P-adj": p_value,
                "Reject": bool(f_stat > f_crit),
            })

    return pd.DataFrame(result_rows)


def add_posthoc_hypotheses(table):
    if table.empty:
        return table

    table = table.copy()
    table["H0"] = "H0: mean(Group1) = mean(Group2)"
    table["H1"] = "H1: mean(Group1) != mean(Group2)"
    if "Reject" in table.columns:
        table["Decision"] = np.where(table["Reject"], "Reject H0", "Fail to reject H0")
    elif "reject" in table.columns:
        table["Decision"] = np.where(table["reject"], "Reject H0", "Fail to reject H0")
    else:
        table["Decision"] = np.where(table.get("P-adj", table.get("P-raw", 1.0)) < 0.05, "Reject H0", "Fail to reject H0")
    return table


def build_posthoc_guide_table(table):
    if table is None or table.empty:
        return pd.DataFrame()

    method = str(table["Method"].iloc[0]) if "Method" in table.columns else "Unknown"
    reason = str(table["Reason"].iloc[0]) if "Reason" in table.columns else "No reason recorded"

    guide_rows = [
        {"Item": "Selected Method", "Value": method},
        {"Item": "Why this method", "Value": reason},
    ]

    if "H0" in table.columns:
        guide_rows.append({"Item": "Null Hypothesis", "Value": str(table["H0"].iloc[0])})
    if "H1" in table.columns:
        guide_rows.append({"Item": "Alternative Hypothesis", "Value": str(table["H1"].iloc[0])})

    guide_rows.append({"Item": "Interpretation Tip", "Value": "Use the decision column to see whether the pairwise null hypothesis was rejected."})
    return pd.DataFrame(guide_rows)


def run_posthoc_test(df_sub, response, group_col, method=None):
    chosen_method = normalize_posthoc_method(method or POSTHOC_METHOD)
    recommendation = suggest_posthoc_test(df_sub, group_col, response)

    if chosen_method == "Recommended":
        chosen_method = recommendation["method"]

    cleaned = df_sub[[group_col, response]].dropna().copy()
    if cleaned[group_col].nunique() < 2:
        return pd.DataFrame()

    if chosen_method == "Tukey HSD":
        tukey = pairwise_tukeyhsd(endog=cleaned[response], groups=cleaned[group_col].astype(str), alpha=0.05)
        tukey_table = pd.DataFrame(tukey.summary().data[1:], columns=tukey.summary().data[0])
        tukey_table.insert(0, "Method", chosen_method)
        tukey_table.insert(1, "Reason", recommendation["reason"])
        tukey_table["H0"] = "H0: mean(Group1) = mean(Group2)"
        tukey_table["H1"] = "H1: mean(Group1) != mean(Group2)"
        tukey_table["Decision"] = np.where(tukey_table["reject"].astype(str).str.lower().isin(["true", "1"]), "Reject H0", "Fail to reject H0")
        return tukey_table

    if chosen_method == "Tukey-Kramer":
        table = _pairwise_tukey_kramer_table(df_sub, response, group_col)
    elif chosen_method == "Duncan":
        table = _pairwise_range_table(df_sub, response, group_col, range_correction="duncan")
    elif chosen_method == "Student-Newman-Keuls":
        table = _pairwise_range_table(df_sub, response, group_col, range_correction="snk")

    if chosen_method == "Bonferroni":
        table = _pairwise_ttest_table(df_sub, response, group_col, "bonferroni", equal_var=False)
    elif chosen_method == "Holm":
        table = _pairwise_ttest_table(df_sub, response, group_col, "holm", equal_var=False)
    elif chosen_method == "Sidak":
        table = _pairwise_ttest_table(df_sub, response, group_col, "sidak", equal_var=False)
    elif chosen_method == "LSD":
        table = _pairwise_ttest_table(df_sub, response, group_col, "none", equal_var=False)
    elif chosen_method == "Games-Howell":
        table = _pairwise_games_howell_table(df_sub, response, group_col)
    elif chosen_method == "Scheffe":
        table = _pairwise_scheffe_table(df_sub, response, group_col)
    else:
        table = _pairwise_ttest_table(df_sub, response, group_col, "holm", equal_var=False)
        chosen_method = "Holm"

    if table.empty:
        return table

    table.insert(0, "Method", chosen_method)
    table.insert(1, "Reason", recommendation["reason"])
    table = add_posthoc_hypotheses(table)
    return table


def run_tukey_posthoc(df_sub, response, group_col):
    return run_posthoc_test(df_sub, response, group_col, method=POSTHOC_METHOD)
