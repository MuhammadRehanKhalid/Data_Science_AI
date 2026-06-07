from src.data_generation import generate_data
from src.train_model import train
from src.evaluate_model import evaluate
from src.visualization import save_scatter
from src.config import TARGET_COLUMNS

"""Interactive pipeline runner.

Features:
- Run individual steps in order
- Move back/forward between steps
- Run all steps
- Exit at any time
"""

steps = [
	{"name": "Generate data", "func": "generate_data"},
	{"name": "Prepare X/y", "func": "prepare_xy"},
	{"name": "Train model", "func": "train"},
	{"name": "Evaluate model", "func": "evaluate"},
	{"name": "Save visualization", "func": "save_scatter"},
	{"name": "Print metrics", "func": "print_metrics"},
]

step_status = {step["name"]: "pending" for step in steps}

DOWNSTREAM_STATE_KEYS = {
	0: ["X", "y", "model", "X_test", "y_test", "results"],
	1: ["model", "X_test", "y_test", "results"],
	2: ["results"],
	3: [],
	4: [],
	5: [],
}

# State holders
state = {
	"df": None,
	"X": None,
	"y": None,
	"model": None,
	"X_test": None,
	"y_test": None,
	"results": None,
}

def run_generate_data():
	print("Running: generate_data()")
	state["df"] = generate_data()
	return True

def run_prepare_xy():
	if state["df"] is None:
		print("Data not generated yet. Please run 'Generate data' first or choose 'run all'.")
		return False
	print("Preparing X and y")
	df = state["df"]
	state["X"] = df.drop(TARGET_COLUMNS, axis=1)
	state["y"] = df[TARGET_COLUMNS]
	return True

def run_train():
	if state["X"] is None or state["y"] is None:
		print("X/y not prepared. Please run 'Prepare X/y' first.")
		return False
	print("Training model...")
	model, X_test, y_test = train(state["X"], state["y"])
	state["model"] = model
	state["X_test"] = X_test
	state["y_test"] = y_test
	return True

def run_evaluate():
	if state["model"] is None or state["X_test"] is None or state["y_test"] is None:
		print("Model or test data missing. Please run 'Train model' first.")
		return False
	print("Evaluating model...")
	state["results"] = evaluate(state["model"], state["X_test"], state["y_test"])
	return True

def run_save_scatter():
	if state["results"] is None or state["y_test"] is None:
		print("Evaluation not done. Please run 'Evaluate model' first.")
		return False
	print("Saving scatter plot...")
	save_scatter(state["y_test"], state["results"]["preds"], target_names=TARGET_COLUMNS)
	return True

def run_print_metrics():
	if state["results"] is None:
		print("No results to print. Please run 'Evaluate model' first.")
		return False
	print("Done")
	print("R2:")
	for target, score in state["results"]["R2"].items():
		print(f"  {target}: {score:.3f}")
	print("RMSE:")
	for target, score in state["results"]["RMSE"].items():
		print(f"  {target}: {score:.2f}")
	return True

FUNC_MAP = {
	"generate_data": run_generate_data,
	"prepare_xy": run_prepare_xy,
	"train": run_train,
	"evaluate": run_evaluate,
	"save_scatter": run_save_scatter,
	"print_metrics": run_print_metrics,
}

def run_step(idx):
	start_idx = idx
	for prior_idx in range(idx):
		if step_status[steps[prior_idx]["name"]] != "complete":
			start_idx = prior_idx
			break

	for current_idx in range(start_idx, idx + 1):
		name = steps[current_idx]["name"]
		func_key = steps[current_idx]["func"]
		print(f"\n--- Step {current_idx+1}/{len(steps)}: {name} ---")
		step_status[name] = "running"
		try:
			completed = FUNC_MAP[func_key]()
		except Exception:
			step_status[name] = "failed"
			raise
		if completed:
			step_status[name] = "complete"
			for state_key in DOWNSTREAM_STATE_KEYS[current_idx]:
				state[state_key] = None
		else:
			step_status[name] = "pending"
			return False

	return True

def run_all_from(start=0):
	actual_start = start
	for prior_idx in range(start):
		if step_status[steps[prior_idx]["name"]] != "complete":
			actual_start = prior_idx
			break

	for i in range(actual_start, len(steps)):
		if not run_step(i):
			break


def show_status(current_idx=0):
	print("\nPipeline steps:")
	for i, s in enumerate(steps):
		mark = ">" if i == current_idx else " "
		status = step_status[s["name"]]
		print(f" {mark} {i+1}. {s['name']} [{status}]")

	print("\nCurrent state summary:")
	for k, v in state.items():
		if v is None:
			description = "---"
		elif hasattr(v, "shape"):
			description = f"set {getattr(v, 'shape', '')}"
		elif isinstance(v, dict):
			description = f"set (keys={len(v)})"
		else:
			description = "set"
		print(f" - {k}: {description}")


def reset_pipeline():
	for key in state:
		state[key] = None
	for step in step_status:
		step_status[step] = "pending"

def interactive_loop():
	print("Interactive pipeline runner")
	idx = 0
	while True:
		show_status(idx)

		print("\nCommands: [r]un, [n]ext, [p]rev, [j]ump, [a]ll, [s]tatus, e[x]it")
		cmd = input("Enter command: ").strip().lower()

		if cmd in ("r", "run"):
			run_step(idx)
		elif cmd in ("n", "next"):
			if idx < len(steps) - 1:
				idx += 1
			else:
				print("Already at last step.")
		elif cmd in ("p", "prev", "b", "back"):
			if idx > 0:
				idx -= 1
			else:
				print("Already at first step.")
		elif cmd in ("j", "jump"):
			to = input("Jump to step number: ").strip()
			if to.isdigit():
				toi = int(to) - 1
				if 0 <= toi < len(steps):
					idx = toi
				else:
					print("Invalid step number.")
			else:
				print("Please enter a number.")
		elif cmd in ("a", "all"):
			run_all_from(idx)
		elif cmd in ("s", "status"):
			show_status(idx)
		elif cmd in ("x", "exit", "q", "quit"):
			print("Exiting pipeline runner.")
			break
		else:
			print("Unknown command.")


if __name__ == '__main__':
	interactive_loop()

