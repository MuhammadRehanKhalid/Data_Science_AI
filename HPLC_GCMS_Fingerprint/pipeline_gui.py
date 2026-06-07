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
from tkinter import filedialog
from tkinter import simpledialog
from pathlib import Path
import tkinter as tk
from tkinter import ttk


ROOT = Path(__file__).resolve().parent

PIPELINE_STEPS = [
    "Step 0: Data Mode",
    "Step 0.5: Biodata",
    "Step 0.6: Load Data",
    "Step 1: Export",
    "Step 3: Ingest",
    "Step 4a: Taxonomy",
    "Step 4c: Optimise",
    "Step 4d: Nested CV",
    "Step 5: ML Train",
    "Step 6: DL Train",
    "Step 7b: Best Model",
    "Step 8: Recommend",
    "Step 9: Figures",
]


class PipelineGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HPLC_GCMS_Fingerprint — Pipeline GUI")
        self.geometry("900x600")

        self.geometry("1600x900")
        self.minsize(1400, 800)

        control_canvas = tk.Canvas(self, highlightthickness=0, height=260)
        control_canvas.pack(fill=tk.X, padx=8, pady=6)
        control_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=control_canvas.xview)
        control_scroll.pack(fill=tk.X, padx=8)
        control_canvas.configure(xscrollcommand=control_scroll.set)

        control_host = ttk.Frame(control_canvas)
        control_canvas.create_window((0, 0), window=control_host, anchor="nw")

        def _update_scroll_region(event):
            control_canvas.configure(scrollregion=control_canvas.bbox("all"))

        control_host.bind("<Configure>", _update_scroll_region)

        frm = ttk.Frame(control_host)
        frm.pack(fill=tk.X, padx=0, pady=0)

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
        self.data_mode = tk.StringVar(value="dummy")
        ttk.Combobox(frm, textvariable=self.data_mode, values=("", "dummy", "real"), width=8).pack(side=tk.LEFT)

        ttk.Label(frm, text="  Real data dir:").pack(side=tk.LEFT, padx=(8,0))
        self.real_data_dir = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.real_data_dir, width=24).pack(side=tk.LEFT)
        ttk.Button(frm, text="Browse", command=self.browse_real_data_dir).pack(side=tk.LEFT, padx=(4,0))
        self.align_samples_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm, text="Align samples", variable=self.align_samples_var).pack(side=tk.LEFT, padx=(6,0))

        ttk.Label(frm, text=" Sources:").pack(side=tk.LEFT, padx=(6,0))
        # Numeric mapping: 1=FTIR, 2=GCMS, 3=HPLC
        self.src_ftir_var = tk.BooleanVar(value=False)
        self.src_gcms_var = tk.BooleanVar(value=False)
        self.src_hplc_var = tk.BooleanVar(value=False)
        self.cb_ftir = ttk.Checkbutton(frm, text="1: FTIR", variable=self.src_ftir_var)
        self.cb_ftir.pack(side=tk.LEFT)
        self.cb_gcms = ttk.Checkbutton(frm, text="2: GCMS", variable=self.src_gcms_var)
        self.cb_gcms.pack(side=tk.LEFT)
        self.cb_hplc = ttk.Checkbutton(frm, text="3: HPLC", variable=self.src_hplc_var)
        self.cb_hplc.pack(side=tk.LEFT)
        # Fallback free-text entry (kept for advanced users)
        self.sources = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.sources, width=16).pack(side=tk.LEFT, padx=(6,0))
        ttk.Label(frm, text="(or enter HPLC,GCMS,FTIR)").pack(side=tk.LEFT)

        # Biodata file selector (to avoid interactive prompts)
        ttk.Label(frm, text="  Biodata:").pack(side=tk.LEFT, padx=(8,0))
        self.biodata_file = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.biodata_file, width=28).pack(side=tk.LEFT)
        ttk.Button(frm, text="Browse", command=self.browse_biodata).pack(side=tk.LEFT, padx=(4,0))
        # Do not auto-override manual selections unless the user opts-in
        self.auto_apply_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Auto-apply detections", variable=self.auto_apply_var, command=self._toggle_auto_apply).pack(side=tk.LEFT, padx=(8,0))

        self.add_biodata_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Add biodata", variable=self.add_biodata_var).pack(side=tk.LEFT, padx=(8,0))

        # DL-specific args
        ttk.Label(frm, text="  DL args:").pack(side=tk.LEFT, padx=(8,0))
        self.dl_args = tk.StringVar(value="")
        ttk.Entry(frm, textvariable=self.dl_args, width=24).pack(side=tk.LEFT)
        # Option to open in an external terminal (real terminal behavior)
        self.external_term_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Open external terminal", variable=self.external_term_var).pack(side=tk.LEFT, padx=(8,0))

        step_frame = ttk.Frame(self)
        step_frame.pack(fill=tk.X, padx=8, pady=(0, 6))
        ttk.Label(step_frame, text="Step focus:").pack(side=tk.LEFT)
        self.current_step_index = tk.IntVar(value=0)
        self.step_focus_var = tk.StringVar(value=PIPELINE_STEPS[0])
        ttk.Label(step_frame, textvariable=self.step_focus_var).pack(side=tk.LEFT, padx=(6, 10))
        ttk.Button(step_frame, text="Back", command=self.step_back).pack(side=tk.LEFT)
        ttk.Button(step_frame, text="Next", command=self.step_next).pack(side=tk.LEFT, padx=(6,0))
        ttk.Button(step_frame, text="Jump", command=self.jump_step).pack(side=tk.LEFT, padx=(6,0))
        ttk.Label(step_frame, text="Status:").pack(side=tk.LEFT, padx=(16,0))
        self.step_status_var = tk.StringVar(value="Idle")
        ttk.Label(step_frame, textvariable=self.step_status_var).pack(side=tk.LEFT, padx=(4,0))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0,6))

        self.run_btn = ttk.Button(btn_frame, text="Run", command=self.start_run)
        self.run_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_run, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Clear", command=self.clear_output).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Exit", command=self.on_exit).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Detect Sources", command=self.detect_sources).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Preview Cmd", command=self.update_command_preview).pack(side=tk.LEFT)

        # Output text
        # Command preview
        preview_frame = ttk.Frame(self)
        preview_frame.pack(fill=tk.X, padx=8, pady=(0,6))
        self.cmd_preview_var = tk.StringVar(value="")
        ttk.Label(preview_frame, text="Command Preview:").pack(side=tk.LEFT)
        ttk.Entry(preview_frame, textvariable=self.cmd_preview_var, width=120).pack(side=tk.LEFT, padx=(6,0), fill=tk.X, expand=True)

        self.step_status_text = tk.Text(self, height=5, wrap=tk.NONE)
        self.step_status_text.pack(fill=tk.X, padx=8, pady=(0,4))
        self.step_status_text.configure(state=tk.DISABLED)

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
        self.step_state = {name: "not started" for name in PIPELINE_STEPS}
        # ensure preview initialized
        self.update_command_preview()
        self.refresh_step_status_panel()

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
        real_dir = self.real_data_dir.get().strip()
        if dm == "real" and real_dir:
            cmd += ["--real-data-dir", real_dir]
        # Selected sources: from numeric checkboxes first, then fallback to free-text
        sel = []
        if self.src_ftir_var.get():
            sel.append("FTIR")
        if self.src_gcms_var.get():
            sel.append("GCMS")
        if self.src_hplc_var.get():
            sel.append("HPLC")
        if not sel:
            srcs = self.sources.get().strip()
            if srcs:
                sel = [s.strip().upper() for s in srcs.split(",") if s.strip()]
        if sel:
            cmd += ["--selected-sources", ",".join(sel)]
        # Biodata file overrides interactive biodata collection
        biodata_path = self.biodata_file.get().strip()
        if biodata_path:
            cmd += ["--biodata-file", biodata_path]
        elif self.add_biodata_var.get():
            cmd += ["--add-biodata"]
        if dm == "dummy" and not biodata_path and not self.add_biodata_var.get():
            cmd += ["--non-interactive"]
        if dm == "real" and self.align_samples_var.get():
            cmd += ["--align-samples"]
        if step:
            cmd += ["--step-display", step]
        # append DL-specific args raw (user provides full CLI tokens like "--epochs 50")
        dl_raw = self.dl_args.get().strip()
        if dl_raw:
            try:
                cmd += shlex.split(dl_raw)
            except Exception:
                cmd += [dl_raw]

        cmdline_preview = ' '.join(shlex.quote(c) for c in cmd)
        self.append_output(f"> Running: {cmdline_preview}\n\n")
        self.set_status("Running")
        self.set_progress(0.0)

        # Start subprocess in background thread
        def _run():
            try:
                # If requested, open an external terminal window (Windows)
                if self.external_term_var.get() and sys.platform.startswith("win"):
                    # Build a single command string and spawn cmd.exe in a new window
                    cmdstr = cmdline_preview
                    self.proc = subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", cmdstr], cwd=str(ROOT))
                    self.append_output("[GUI] Launched external terminal. Output will appear in the new window.\n")
                    self.set_status("Running")
                    self.set_step_status("running")
                    return
                else:
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
                self.set_step_status("running")
                self.mark_step_running("Step 0: Data Mode")

                for line in self.proc.stdout:
                    self.append_output(line)
                    self.mark_step_status_from_output(line)
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
                    self.set_step_status("completed")
                else:
                    self.set_status("Failed")
                    self.set_step_status("failed")

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

    def update_command_preview(self):
        display = self.display_var.get()
        step = self.step_override.get().strip()
        cmd = [sys.executable, str(ROOT / "run_pipeline.py"), "--training-display", display]
        dm = self.data_mode.get().strip()
        if dm:
            cmd += ["--data-mode", dm]
        # assemble selected sources from checkboxes or free-text
        sel = []
        if self.src_ftir_var.get():
            sel.append("FTIR")
        if self.src_gcms_var.get():
            sel.append("GCMS")
        if self.src_hplc_var.get():
            sel.append("HPLC")
        if not sel:
            srcs = self.sources.get().strip()
            if srcs:
                sel = [s.strip().upper() for s in srcs.split(",") if s.strip()]
        if sel:
            cmd += ["--selected-sources", ",".join(sel)]
        # biodata file preferred over interactive add-biodata
        biodata_path = self.biodata_file.get().strip()
        if biodata_path:
            cmd += ["--biodata-file", biodata_path]
        elif self.add_biodata_var.get():
            cmd += ["--add-biodata"]
        if dm == "dummy" and not biodata_path and not self.add_biodata_var.get():
            cmd += ["--non-interactive"]
        if step:
            cmd += ["--step-display", step]
        # present a shell-escaped preview
        try:
            preview = " ".join(shlex.quote(c) for c in cmd)
        except Exception:
            preview = " ".join(cmd)
        self.cmd_preview_var.set(preview)

    def browse_biodata(self):
        path = filedialog.askopenfilename(title="Select biodata file", filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*")])
        if path:
            self.biodata_file.set(path)
            self.append_output(f"[GUI] Selected biodata file: {path}\n")
            self.update_command_preview()

    def browse_real_data_dir(self):
        path = filedialog.askdirectory(title="Select real data directory")
        if path:
            self.real_data_dir.set(path)
            self.append_output(f"[GUI] Selected real data directory: {path}\n")
            self.update_command_preview()

    def step_back(self):
        idx = max(0, self.current_step_index.get() - 1)
        self.current_step_index.set(idx)
        self.step_focus_var.set(PIPELINE_STEPS[idx])
        self.append_output(f"[GUI] Focused step: {PIPELINE_STEPS[idx]}\n")

    def step_next(self):
        idx = min(len(PIPELINE_STEPS) - 1, self.current_step_index.get() + 1)
        self.current_step_index.set(idx)
        self.step_focus_var.set(PIPELINE_STEPS[idx])
        self.append_output(f"[GUI] Focused step: {PIPELINE_STEPS[idx]}\n")

    def jump_step(self):
        choice = simpledialog.askinteger("Jump to Step", f"Choose step index 0 to {len(PIPELINE_STEPS)-1}")
        if choice is None:
            return
        idx = max(0, min(len(PIPELINE_STEPS) - 1, int(choice)))
        self.current_step_index.set(idx)
        self.step_focus_var.set(PIPELINE_STEPS[idx])
        self.append_output(f"[GUI] Focused step: {PIPELINE_STEPS[idx]}\n")

    def set_step_status(self, text: str):
        self.step_status_var.set(text)
        self.refresh_step_status_panel()

    def mark_step_running(self, step_name: str):
        self.step_state[step_name] = "running"
        self.refresh_step_status_panel()

    def mark_step_status_from_output(self, line: str):
        lower = line.lower()
        matched = None
        for step_name in PIPELINE_STEPS:
            token = step_name.split(":", 1)[0].lower()
            if token in lower:
                matched = step_name
                break
        if matched is None:
            return
        if "failed" in lower or "error" in lower:
            self.step_state[matched] = "failed"
        elif any(k in lower for k in ["completed", "[ok]", "generated", "wrote", "loaded"]):
            self.step_state[matched] = "done"
        else:
            self.step_state[matched] = "running"
        self.refresh_step_status_panel()

    def refresh_step_status_panel(self):
        try:
            self.step_status_text.configure(state=tk.NORMAL)
            self.step_status_text.delete("1.0", tk.END)
            for step_name in PIPELINE_STEPS:
                self.step_status_text.insert(tk.END, f"{step_name}: {self.step_state.get(step_name, 'not started')}\n")
            self.step_status_text.configure(state=tk.DISABLED)
        except Exception:
            pass

    def detect_sources(self):
        selected = self._selected_sources_from_checkboxes()
        if selected:
            # Keep the free-text field in sync with exactly what the checkboxes say.
            self.sources.set(",".join(selected))
            self.append_output(f"[GUI] Selected sources: {', '.join(selected)}\n")
        else:
            self.sources.set("")
            self.append_output("[GUI] No sources selected. Choose FTIR, GCMS, HPLC, or any combination.\n")
        self.update_command_preview()

    def _selected_sources_from_checkboxes(self):
        selected = []
        if self.src_ftir_var.get():
            selected.append("FTIR")
        if self.src_gcms_var.get():
            selected.append("GCMS")
        if self.src_hplc_var.get():
            selected.append("HPLC")
        return selected

    def _toggle_auto_apply(self):
        # If auto-apply becomes false, ensure checkbuttons are enabled for manual edits
        try:
            if self.auto_apply_var.get():
                # disable manual edit (user has chosen auto-apply)
                self.cb_ftir.config(state=tk.DISABLED)
                self.cb_gcms.config(state=tk.DISABLED)
                self.cb_hplc.config(state=tk.DISABLED)
            else:
                self.cb_ftir.config(state=tk.NORMAL)
                self.cb_gcms.config(state=tk.NORMAL)
                self.cb_hplc.config(state=tk.NORMAL)
        except Exception:
            pass


if __name__ == "__main__":
    app = PipelineGUI()
    app.mainloop()
