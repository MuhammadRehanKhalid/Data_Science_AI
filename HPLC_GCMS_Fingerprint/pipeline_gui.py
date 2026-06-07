"""Simple Tkinter GUI to launch the pipeline and view terminal output.

This lightweight launcher runs `run_pipeline.py` in a subprocess and streams
stdout/stderr into a text widget. It also exposes `--training-display` and
`--step-display` options so you can select compact progress or verbose logs.

Usage: python pipeline_gui.py
"""
from __future__ import annotations

import threading
import subprocess
import sys
import shlex
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk


ROOT = Path(__file__).resolve().parent


class PipelineGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HPLC_GCMS_Fingerprint — Pipeline GUI")
        self.geometry("900x600")

        frm = ttk.Frame(self)
        frm.pack(fill=tk.X, padx=8, pady=6)

        ttk.Label(frm, text="Training display:").pack(side=tk.LEFT)
        self.display_var = tk.StringVar(value="verbose")
        ttk.Radiobutton(frm, text="Verbose", value="verbose", variable=self.display_var).pack(side=tk.LEFT)
        ttk.Radiobutton(frm, text="Progress", value="progress", variable=self.display_var).pack(side=tk.LEFT)

        ttk.Label(frm, text="  Step overrides:").pack(side=tk.LEFT, padx=(10,0))
        self.step_override = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.step_override, width=24).pack(side=tk.LEFT)
        ttk.Label(frm, text=" e.g. 5:progress,6:verbose").pack(side=tk.LEFT)

        # Non-interactive options
        ttk.Label(frm, text="   Data mode:").pack(side=tk.LEFT, padx=(10,0))
        self.data_mode = tk.StringVar(value="")
        ttk.Combobox(frm, textvariable=self.data_mode, values=("", "dummy", "real"), width=8).pack(side=tk.LEFT)

        ttk.Label(frm, text=" Sources:").pack(side=tk.LEFT, padx=(6,0))
        self.sources = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.sources, width=20).pack(side=tk.LEFT)
        ttk.Label(frm, text=" e.g. HPLC,GCMS").pack(side=tk.LEFT)

        self.add_biodata_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Add biodata", variable=self.add_biodata_var).pack(side=tk.LEFT, padx=(8,0))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0,6))

        self.run_btn = ttk.Button(btn_frame, text="Run", command=self.start_run)
        self.run_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_run, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Clear", command=self.clear_output).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Exit", command=self.on_exit).pack(side=tk.RIGHT)

        # Output text
        self.output = tk.Text(self, wrap=tk.NONE)
        self.output.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Progress and status
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=8, pady=(0,6))
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=(4,20))

        ttk.Label(status_frame, text="Progress:").pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=240, mode="determinate", variable=self.progress_var, maximum=100.0)
        self.progress_bar.pack(side=tk.LEFT, padx=(4,0))

        # Internal
        self.proc = None
        self._thread = None

    def start_run(self):
        if self.proc is not None:
            return
        display = self.display_var.get()
        step = self.step_override.get().strip()
        cmd = [sys.executable, str(ROOT / "run_pipeline.py")]
        cmd += ["--training-display", display]
        # Non-interactive flags
        dm = self.data_mode.get().strip()
        if dm:
            cmd += ["--data-mode", dm]
        srcs = self.sources.get().strip()
        if srcs:
            cmd += ["--selected-sources", srcs]
        if self.add_biodata_var.get():
            cmd += ["--add-biodata"]
        if step:
            cmd += ["--step-display", step]

        self.append_output(f"> Running: {' '.join(shlex.quote(c) for c in cmd)}\n\n")
        self.set_status("Running")
        self.set_progress(0.0)

        # Start subprocess in background thread
        def _run():
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    cwd=str(ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                )
                self.run_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)

                for line in self.proc.stdout:
                    self.append_output(line)
                    # Try to parse a percent like '42.50%' from the line
                    m = re.search(r"(\d+(?:\.\d+)?)%", line)
                    if m:
                        try:
                            pct = float(m.group(1))
                            self.set_progress(pct)
                        except Exception:
                            pass

                self.proc.wait()
                rc = self.proc.returncode
                self.append_output(f"\nProcess exited with return code {rc}\n")
                if rc == 0:
                    self.set_status("Completed")
                    self.set_progress(100.0)
                else:
                    self.set_status("Failed")

            except Exception as e:
                self.append_output(f"[ERROR] {e}\n")
            finally:
                self.proc = None
                self.run_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop_run(self):
        if self.proc is None:
            return
        try:
            self.proc.terminate()
            self.append_output("\n[Stopping process]\n")
        except Exception as e:
            self.append_output(f"[ERROR stopping] {e}\n")

    def append_output(self, text: str):
        # Thread-safe append
        def _append():
            self.output.insert(tk.END, text)
            self.output.see(tk.END)
        try:
            self.output.after(0, _append)
        except Exception:
            pass

    def set_progress(self, pct: float):
        def _set():
            try:
                self.progress_var.set(max(0.0, min(100.0, float(pct))))
            except Exception:
                self.progress_var.set(0.0)
        try:
            self.progress_bar.after(0, _set)
        except Exception:
            pass

    def set_status(self, text: str):
        def _set():
            self.status_var.set(text)
        try:
            self.status_label.after(0, _set)
        except Exception:
            pass

    def clear_output(self):
        self.output.delete("1.0", tk.END)

    def on_exit(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = PipelineGUI()
    app.mainloop()
