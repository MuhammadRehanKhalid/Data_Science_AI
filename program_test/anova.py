import pandas as pd
from scipy import stats

def one_way_anova(df, group_col, value_col):
    groups = [group[value_col].values for _, group in df.groupby(group_col)]
    f_stat, p_val = stats.f_oneway(*groups)
    return f_stat, p_val
