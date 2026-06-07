import contextlib
import io
import traceback
import tkinter as tk
from tkinter import messagebox, scrolledtext

import run_pipeline as pipeline


class PipelineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Algae Antioxidant Pipeline")
        self.root.geometry("920x640")

        self.current_idx = 0

        self.header = tk.Label(
            root,
            text="Algae Antioxidant Pipeline",
            font=("Arial", 18, "bold"),
        )
        self.header.pack(pady=(12, 4))

        self.subheader = tk.Label(
            root,
            text="Use the buttons to move through the pipeline, run steps, and view status.",
            font=("Arial", 10),
        )
        self.subheader.pack(pady=(0, 10))

        self.steps_frame = tk.Frame(root)
        self.steps_frame.pack(fill="x", padx=12)

        self.steps_list = tk.Listbox(self.steps_frame, height=8, font=("Consolas", 11))
        self.steps_list.pack(fill="x", expand=True)

        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(fill="x", padx=12, pady=10)

        self._add_button("Back", self.go_back)
        self._add_button("Next", self.go_next)
        self._add_button("Run Current Step", self.run_current)
        self._add_button("Run All", self.run_all)
        self._add_button("Status", self.show_status)
        self._add_button("Reset", self.reset_pipeline)
        self._add_button("Exit", self.exit_app)

        self.output = scrolledtext.ScrolledText(root, height=18, font=("Consolas", 10))
        self.output.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.refresh_view()
        self.log("Pipeline UI ready.")

    def _add_button(self, label, command):
        button = tk.Button(self.buttons_frame, text=label, command=command, width=16)
        button.pack(side="left", padx=4, pady=4)

    def log(self, text):
        self.output.insert(tk.END, f"{text}\n")
        self.output.see(tk.END)

    def capture_action(self, action):
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                result = action()
        except Exception:
            captured = buffer.getvalue().rstrip()
            if captured:
                self.log(captured)
            self.log(traceback.format_exc().rstrip())
            messagebox.showerror("Pipeline error", "A pipeline step failed. See the output pane for details.")
            return None

        captured = buffer.getvalue().rstrip()
        if captured:
            self.log(captured)
        return result

    def refresh_view(self):
        self.steps_list.delete(0, tk.END)
        for index, step in enumerate(pipeline.steps):
            marker = ">" if index == self.current_idx else " "
            status = pipeline.step_status[step["name"]]
            self.steps_list.insert(tk.END, f"{marker} {index + 1}. {step['name']} [{status}]")

    def go_back(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.log(f"Moved back to step {self.current_idx + 1}.")
        else:
            self.log("Already at the first step.")
        self.refresh_view()

    def go_next(self):
        if self.current_idx < len(pipeline.steps) - 1:
            self.current_idx += 1
            self.log(f"Moved next to step {self.current_idx + 1}.")
        else:
            self.log("Already at the last step.")
        self.refresh_view()

    def run_current(self):
        self.log(f"Running step {self.current_idx + 1}: {pipeline.steps[self.current_idx]['name']}")
        self.capture_action(lambda: pipeline.run_step(self.current_idx))
        self.refresh_view()

    def run_all(self):
        self.log(f"Running pipeline from step {self.current_idx + 1}.")
        self.capture_action(lambda: pipeline.run_all_from(self.current_idx))
        self.refresh_view()

    def show_status(self):
        self.capture_action(lambda: pipeline.show_status(self.current_idx))
        self.refresh_view()

    def reset_pipeline(self):
        pipeline.reset_pipeline()
        self.current_idx = 0
        self.log("Pipeline reset.")
        self.refresh_view()

    def exit_app(self):
        self.log("Exiting pipeline app.")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PipelineApp(root)
    root.mainloop()
