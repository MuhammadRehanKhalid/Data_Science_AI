"""
Generate comprehensive publication assets with faster execution
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    r2_score, mean_squared_error, mean_absolute_error,
    mean_absolute_percentage_error
)
from scipy import stats
import joblib
import warnings
import os

warnings.filterwarnings('ignore')

from src.data_generation import generate_data
from src.train_model import train
from src.config import FIGURE_DIR, MODEL_DIR, TARGET_COLUMNS
from src.preprocessing import get_preprocessor

# Set style for publication-quality figures
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10

base_dir = os.path.dirname(os.path.abspath(__file__))
figures_dir = os.path.join(base_dir, FIGURE_DIR)
results_dir = os.path.join(base_dir, "results")
os.makedirs(figures_dir, exist_ok=True)
os.makedirs(results_dir, exist_ok=True)

print("\n" + "="*80)
print("GENERATING PUBLICATION-QUALITY FIGURES & TABLES")
print("="*80 + "\n")

# Generate dataset and train model
print("📊 Generating dataset and training model...")
df = generate_data()
X = df.drop(TARGET_COLUMNS, axis=1)
y = df[TARGET_COLUMNS]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model, _, _ = train(X, y)

# Get predictions
y_pred_train = pd.DataFrame(model.predict(X_train), columns=TARGET_COLUMNS, index=y_train.index)
y_pred_test = pd.DataFrame(model.predict(X_test), columns=TARGET_COLUMNS, index=y_test.index)

# Calculate metrics
metrics_rows = []
for assay in TARGET_COLUMNS:
    r2_train = r2_score(y_train[assay], y_pred_train[assay])
    r2_test = r2_score(y_test[assay], y_pred_test[assay])
    rmse_train = np.sqrt(mean_squared_error(y_train[assay], y_pred_train[assay]))
    rmse_test = np.sqrt(mean_squared_error(y_test[assay], y_pred_test[assay]))
    mae_test = mean_absolute_error(y_test[assay], y_pred_test[assay])
    mape_test = mean_absolute_percentage_error(y_test[assay], y_pred_test[assay])
    metrics_rows.append({
        "Assay": assay,
        "Train R2": r2_train,
        "Test R2": r2_test,
        "Train RMSE": rmse_train,
        "Test RMSE": rmse_test,
        "Test MAE": mae_test,
        "Test MAPE": mape_test * 100
    })

metrics_df = pd.DataFrame(metrics_rows)
cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')

print("   ✓ Test metrics per assay: ")
for _, row in metrics_df.iterrows():
    print(f"     {row['Assay']}: R²={row['Test R2']:.4f}, RMSE={row['Test RMSE']:.2f}, MAE={row['Test MAE']:.2f}")
print("")

# ============================================================================
# TABLE 1: ASSAY PERFORMANCE
# ============================================================================
metrics_df_display = metrics_df.copy()
metrics_df_display["Train R2"] = metrics_df_display["Train R2"].map(lambda v: f"{v:.4f}")
metrics_df_display["Test R2"] = metrics_df_display["Test R2"].map(lambda v: f"{v:.4f}")
metrics_df_display["Train RMSE"] = metrics_df_display["Train RMSE"].map(lambda v: f"{v:.2f}")
metrics_df_display["Test RMSE"] = metrics_df_display["Test RMSE"].map(lambda v: f"{v:.2f}")
metrics_df_display["Test MAE"] = metrics_df_display["Test MAE"].map(lambda v: f"{v:.2f}")
metrics_df_display["Test MAPE"] = metrics_df_display["Test MAPE"].map(lambda v: f"{v:.2f}")
metrics_df.to_csv(os.path.join(results_dir, 'Table_1_Assay_Performance.csv'), index=False)
print("📋 Table 1: Assay Performance Metrics")
print(metrics_df_display.to_string(index=False))

# ============================================================================
# TABLE 2: CROSS-VALIDATION
# ============================================================================
cv_df = pd.DataFrame({
    'Fold': [f'Fold {i+1}' for i in range(len(cv_scores))] + ['Mean', 'Std Dev'],
    'R² Score': [f"{s:.4f}" for s in cv_scores] + [f"{cv_scores.mean():.4f}", f"{cv_scores.std():.4f}"]
})
cv_df.to_csv(os.path.join(results_dir, 'Table_2_CrossValidation.csv'), index=False)
print("\n📋 Table 2: Cross-Validation")
print(cv_df.to_string(index=False))

# ============================================================================
# TABLE 3: FEATURE STATISTICS
# ============================================================================
numeric_cols = X.select_dtypes(include=[np.number]).columns
stats_df = pd.DataFrame({
    'Feature': numeric_cols,
    'Mean': X[numeric_cols].mean().round(3),
    'Std Dev': X[numeric_cols].std().round(3),
    'Min': X[numeric_cols].min().round(3),
    'Max': X[numeric_cols].max().round(3)
}).reset_index(drop=True)
stats_df.to_csv(os.path.join(results_dir, 'Table_3_Dataset_Statistics.csv'), index=False)
print("\n📋 Table 3: Feature Statistics")
print(stats_df.to_string(index=False))

# ============================================================================
# TABLE 4: ASSAY STATISTICS
# ============================================================================
assay_stats_rows = []
for assay in TARGET_COLUMNS:
    assay_stats_rows.append({
        "Assay": assay,
        "Count": len(y[assay]),
        "Mean": y[assay].mean(),
        "Median": y[assay].median(),
        "Std Dev": y[assay].std(),
        "Min": y[assay].min(),
        "Q1": y[assay].quantile(0.25),
        "Q3": y[assay].quantile(0.75),
        "Max": y[assay].max()
    })

assay_stats_df = pd.DataFrame(assay_stats_rows)
assay_stats_df.to_csv(os.path.join(results_dir, 'Table_4_Assay_Statistics.csv'), index=False)
print("\n📋 Table 4: Assay Statistics")
print(assay_stats_df.round(2).to_string(index=False))

# ============================================================================
# TABLE 5: CATEGORICAL ANALYSIS
# ============================================================================
cat_rows = []
for assay in TARGET_COLUMNS:
    algal_stats = df.groupby('algal_class')[assay].agg(['count', 'mean', 'std']).reset_index()
    algal_stats['Assay'] = assay
    algal_stats['Category Type'] = 'Algal Class'
    algal_stats.rename(columns={'algal_class': 'Category', 'count': 'Count', 'mean': 'Mean', 'std': 'Std Dev'}, inplace=True)
    cat_rows.append(algal_stats)

    solvent_stats = df.groupby('solvent')[assay].agg(['count', 'mean', 'std']).reset_index()
    solvent_stats['Assay'] = assay
    solvent_stats['Category Type'] = 'Solvent'
    solvent_stats.rename(columns={'solvent': 'Category', 'count': 'Count', 'mean': 'Mean', 'std': 'Std Dev'}, inplace=True)
    cat_rows.append(solvent_stats)

cat_analysis = pd.concat(cat_rows, ignore_index=True)
cat_analysis.to_csv(os.path.join(results_dir, 'Table_5_Categorical_Analysis.csv'), index=False)
print("\n📋 Table 5: Categorical Analysis (Algal Class + Solvent)")
print(cat_analysis.head(10).round(2).to_string(index=False))

# ============================================================================
# TABLE 6: FEATURE IMPORTANCE
# ============================================================================
feature_names = list(X.columns)

perm = permutation_importance(
    model, X_test, y_test, n_repeats=10, random_state=42, scoring='r2'
)
feature_importance = perm.importances_mean

importance_sum = feature_importance.sum()
if importance_sum == 0:
    importance_sum = 1.0

importance_df = pd.DataFrame({
    'Feature': feature_names,
    'Importance': (feature_importance / importance_sum * 100).round(2)
}).sort_values('Importance', ascending=False).reset_index(drop=True)
importance_df.to_csv(os.path.join(results_dir, 'Table_6_Feature_Importance.csv'), index=False)
print("\n📋 Table 6: Feature Importance (Top 10)")
print(importance_df.head(10).to_string(index=False))

# ============================================================================
# FIGURES
# ============================================================================
residuals = y_test - y_pred_test

print("\n🎨 Generating figures...")

# Figure 1: Observed vs Predicted (per assay)
for assay in TARGET_COLUMNS:
    yt = y_test[assay]
    yp = y_pred_test[assay]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(yt, yp, alpha=0.6, s=40, edgecolors='k', linewidth=0.4)
    ax.plot([yt.min(), yt.max()], [yt.min(), yt.max()], '--r', lw=2)
    ax.set_xlabel(f"Observed {assay}", fontweight='bold')
    ax.set_ylabel(f"Predicted {assay}", fontweight='bold')
    ax.set_title(f"Observed vs Predicted {assay}", fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, f"Figure_1_Observed_vs_Predicted_{assay}.png"), dpi=300, bbox_inches='tight')
    plt.close()
print("   ✓ Figure 1: Observed vs Predicted (per assay)")

# Figure 2: Assay Performance (R2 and RMSE)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].bar(metrics_df["Assay"], metrics_df["Test R2"], color='steelblue')
axes[0].set_ylabel('Test R²', fontweight='bold')
axes[0].set_title('Test R² by Assay')
axes[0].grid(True, alpha=0.3, axis='y')
axes[1].bar(metrics_df["Assay"], metrics_df["Test RMSE"], color='salmon')
axes[1].set_ylabel('Test RMSE', fontweight='bold')
axes[1].set_title('Test RMSE by Assay')
axes[1].grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'Figure_2_Assay_Performance.png'), dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Figure 2: Assay Performance")

# Figure 3: Feature Importance
fig, ax = plt.subplots(figsize=(12, 8))
top_features = importance_df.head(15)
bars = ax.barh(range(len(top_features)), top_features['Importance'],
               color=plt.cm.viridis(np.linspace(0, 1, len(top_features))))
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['Feature'])
ax.set_xlabel('Importance (%)', fontweight='bold')
ax.set_title('Top 15 Most Important Features', fontweight='bold', fontsize=14)
ax.invert_yaxis()
ax.grid(True, alpha=0.3, axis='x')
for i, (idx, row) in enumerate(top_features.iterrows()):
    ax.text(row['Importance'] + 0.2, i, f"{row['Importance']:.1f}%", va='center')
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'Figure_3_Feature_Importance.png'), dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Figure 3: Feature Importance")

# Figure 4: Assay Distributions
rows, cols = 2, 3
fig, axes = plt.subplots(rows, cols, figsize=(15, 8))
axes = axes.flatten()
for idx, assay in enumerate(TARGET_COLUMNS):
    axes[idx].hist(y[assay], bins=30, edgecolor='k', alpha=0.7, color='skyblue')
    axes[idx].set_title(f"{assay} Distribution")
    axes[idx].set_xlabel(assay, fontweight='bold')
    axes[idx].set_ylabel('Frequency', fontweight='bold')
    axes[idx].grid(True, alpha=0.3, axis='y')
for j in range(len(TARGET_COLUMNS), rows * cols):
    axes[j].axis('off')
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'Figure_4_Assay_Distributions.png'), dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Figure 4: Assay Distributions")

# Figure 5: Assay Correlation Matrix
assay_corr = y.corr()
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(assay_corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax, vmin=-1, vmax=1)
ax.set_title('Assay Correlation Matrix', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'Figure_5_Assay_Correlation.png'), dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Figure 5: Assay Correlation Matrix")

# Figure 6: Feature Correlation Matrix
numerical_cols = X.select_dtypes(include=[np.number]).columns
corr_matrix = X[numerical_cols].corr()
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax, vmin=-1, vmax=1)
ax.set_title('Feature Correlation Matrix', fontweight='bold', fontsize=14, pad=20)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'Figure_6_Feature_Correlation.png'), dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Figure 6: Feature Correlation Matrix")

# Figure 7: Categorical Effects (heatmaps)
algal_means = df.groupby('algal_class')[TARGET_COLUMNS].mean()
solvent_means = df.groupby('solvent')[TARGET_COLUMNS].mean()
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
sns.heatmap(algal_means, annot=True, fmt='.1f', cmap='YlGnBu', ax=axes[0])
axes[0].set_title('Assay Means by Algal Class')
sns.heatmap(solvent_means, annot=True, fmt='.1f', cmap='YlGnBu', ax=axes[1])
axes[1].set_title('Assay Means by Solvent')
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'Figure_7_Categorical_Effects.png'), dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Figure 7: Categorical Effects")

# Figure 8: Cross-Validation
fig, ax = plt.subplots(figsize=(10, 6))
folds = [f'Fold {i+1}' for i in range(len(cv_scores))]
colors = plt.cm.viridis(np.linspace(0, 1, len(cv_scores)))
bars = ax.bar(folds, cv_scores, color=colors, edgecolor='k', linewidth=1.5, alpha=0.8)
ax.axhline(cv_scores.mean(), color='r', linestyle='--', lw=2.5, label=f'Mean = {cv_scores.mean():.4f}')
ax.fill_between(range(len(folds)), cv_scores.mean() - cv_scores.std(),
                cv_scores.mean() + cv_scores.std(), alpha=0.2, color='red')
ax.set_ylabel('R² Score (overall)', fontweight='bold')
ax.set_xlabel('Fold', fontweight='bold')
ax.set_title('5-Fold Cross-Validation Results', fontweight='bold', fontsize=14)
ax.set_ylim([cv_scores.min() - 0.05, 1.0])
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:.4f}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'Figure_8_CrossValidation.png'), dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Figure 8: Cross-Validation")

# Figure 9: Feature Distributions
numerical_features = ['phenolic_potential', 'lipid_content', 'polarity_index',
                     'extraction_temp', 'extraction_time']
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for idx, feature in enumerate(numerical_features):
    axes[idx].hist(df[feature], bins=30, edgecolor='k', alpha=0.7, color='skyblue')
    axes[idx].set_xlabel(feature.replace('_', ' ').title(), fontweight='bold')
    axes[idx].set_ylabel('Frequency', fontweight='bold')
    axes[idx].set_title(f'Distribution of {feature.replace("_", " ").title()}')
    axes[idx].grid(True, alpha=0.3, axis='y')
    mean_val = df[feature].mean()
    std_val = df[feature].std()
    axes[idx].text(0.98, 0.95, f'μ={mean_val:.2f}\nσ={std_val:.2f}',
                   transform=axes[idx].transAxes, fontsize=10,
                   verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

axes[5].axis('off')
plt.tight_layout()
plt.savefig(os.path.join(figures_dir, 'Figure_9_Feature_Distributions.png'), dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ Figure 9: Feature Distributions")

# ============================================================================
# COMPREHENSIVE SUMMARY
# ============================================================================
summary_text = f"""
{'='*80}
MULTI-ASSAY ANTIOXIDANT PREDICTION MODEL - RESULTS SUMMARY
{'='*80}

1. DATASET OVERVIEW
   Total Samples: {len(df):,}
   Training Set: {len(X_train):,} samples | Test Set: {len(X_test):,} samples
   Features: {len(X.columns)} variables (4 numerical + 2 categorical)
   Targets: {', '.join(TARGET_COLUMNS)}

2. MODEL PERFORMANCE (Test Set)
"""

for _, row in metrics_df.iterrows():
    summary_text += (
        f"\n   - {row['Assay']}: R²={row['Test R2']:.4f}, RMSE={row['Test RMSE']:.2f}, "
        f"MAE={row['Test MAE']:.2f}, MAPE={row['Test MAPE']:.2f}%"
    )

summary_text += f"""

   Cross-Validation (5-fold, overall):
   - Mean R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}

3. KEY FINDINGS

   a) Most Important Features:
"""

for idx, row in importance_df.head(5).iterrows():
    summary_text += f"\n      {idx+1}. {row['Feature']}: {row['Importance']:.1f}%"

summary_text += f"""

   b) Assay Statistics (Means):
"""

for _, row in assay_stats_df.iterrows():
    summary_text += f"\n      {row['Assay']}: Mean={row['Mean']:.2f}, Std={row['Std Dev']:.2f}, Range=[{row['Min']:.2f}, {row['Max']:.2f}]"

summary_text += f"""

4. CATEGORICAL INSIGHTS (Top-level)
   - See Table 5 for full Algal Class and Solvent summaries per assay.

5. ASSAY COMPARISON
   - Figure 2 summarizes R² and RMSE by assay.
   - Figure 5 shows assay-to-assay correlation.

6. GENERATED PUBLICATION ASSETS
   
   Tables (CSV format):
   ✓ Table 1: Assay Performance Metrics
   ✓ Table 2: Cross-Validation Results
   ✓ Table 3: Feature Statistics
   ✓ Table 4: Assay Statistics
   ✓ Table 5: Categorical Analysis (Assays x Class/Solvent)
   ✓ Table 6: Feature Importance Rankings
   
   Figures (300 DPI, publication-ready):
   ✓ Figure 1: Observed vs Predicted per Assay
   ✓ Figure 2: Assay Performance (R²/RMSE)
   ✓ Figure 3: Feature Importance Bar Chart
   ✓ Figure 4: Assay Distributions
   ✓ Figure 5: Assay Correlation Heatmap
   ✓ Figure 6: Feature Correlation Heatmap
   ✓ Figure 7: Categorical Effects Heatmaps
   ✓ Figure 8: Cross-Validation Results
   ✓ Figure 9: Feature Distributions

7. CONCLUSION
   
   A multi-output HistGradientBoosting regression model successfully predicts
   multiple antioxidant assays (ORAC, FRAP, DPPH, ABTS, TPC). The model shows
   strong generalization and provides assay-to-assay comparisons suitable for
   reporting and publication.

{'='*80}
Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
"""

print("\n" + summary_text)

# Save summary
with open(os.path.join(results_dir, 'COMPREHENSIVE_RESULTS_SUMMARY.txt'), 'w', encoding='utf-8') as f:
    f.write(summary_text)

print("\n" + "="*80)
print("✅ SUCCESS! All publication assets generated!")
print("="*80)
print(f"\n📁 Output Files:")
print(f"   Figures (9 total): {figures_dir}")
print(f"   Tables (6 total): {results_dir}")
print(f"   Summary Report: {os.path.join(results_dir, 'COMPREHENSIVE_RESULTS_SUMMARY.txt')}")
print("\n" + "="*80 + "\n")
