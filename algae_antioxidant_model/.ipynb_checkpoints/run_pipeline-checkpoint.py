from src.data_generation import generate_data
from src.train_model import train
from src.evaluate_model import evaluate
from src.visualization import save_scatter
from src.config import TARGET_COLUMNS

print("🚀 Running full pipeline...")

df = generate_data()
X = df.drop(TARGET_COLUMNS, axis=1)
y = df[TARGET_COLUMNS]

model, X_test, y_test = train(X, y)
results = evaluate(model, X_test, y_test)

save_scatter(y_test, results['preds'], target_names=TARGET_COLUMNS)

print("✅ Done")
print("R2:")
for target, score in results["R2"].items():
	print(f"  {target}: {score:.3f}")
print("RMSE:")
for target, score in results["RMSE"].items():
	print(f"  {target}: {score:.2f}")
