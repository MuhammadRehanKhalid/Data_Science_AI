import scipy.stats as stats

def one_way_anova(df, group_col, value_col):
    """
    Perform one-way ANOVA.
    Args:
        df: DataFrame
        group_col: column name for group/factor
        value_col: column name for response/values
    Returns:
        F-statistic, p-value
    """
    groups = [group[value_col].values for name, group in df.groupby(group_col)]
    f_stat, p_val = stats.f_oneway(*groups)
    return f_stat, p_val