from __future__ import annotations

import builtins
import contextlib
import io
import os
import queue
import sys
import threading
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox


def _project_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


PROJECT_ROOT = _project_root()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

import run_pipeline


class QueueWriter:
    def __init__(self, output_queue: queue.Queue[str]):
        self.output_queue = output_queue

    def write(self, text: str) -> int:
        if text:
            self.output_queue.put(text)
        return len(text)

    def flush(self) -> None:
        return None


class PipelineGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title('HPLC / GC-MS Pipeline Launcher')
        self.geometry('1080x760')
        self.minsize(960, 680)

        self.output_queue: queue.Queue[str | tuple[str, str]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.pipeline_running = False

        self.data_mode = tk.StringVar(value='dummy')
        self.skip_dl = tk.BooleanVar(value=False)
        self.validate_species = tk.BooleanVar(value=False)
        self.ftir = tk.BooleanVar(value=True)
        self.hplc = tk.BooleanVar(value=True)
        self.gcms = tk.BooleanVar(value=True)
        self.reps = tk.StringVar(value='15')
        self.epochs = tk.StringVar(value='200')
        self.batch_size = tk.StringVar(value='16')

        self._build_ui()
        self._poll_queue()

    def _build_ui(self) -> None:
        self.configure(bg='#0c1118')

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Root.TFrame', background='#0c1118')
        style.configure('Card.TFrame', background='#111826', relief='flat')
        style.configure('Header.TLabel', background='#0c1118', foreground='#f5f7fb', font=('Segoe UI', 20, 'bold'))
        style.configure('Subtle.TLabel', background='#0c1118', foreground='#9fb0c8', font=('Segoe UI', 10))
        style.configure('CardTitle.TLabel', background='#111826', foreground='#f5f7fb', font=('Segoe UI', 12, 'bold'))
        style.configure('CardText.TLabel', background='#111826', foreground='#c6d0e0', font=('Segoe UI', 10))
        style.configure('TCheckbutton', background='#111826', foreground='#d7deea', font=('Segoe UI', 10))
        style.configure('TRadiobutton', background='#111826', foreground='#d7deea', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=(14, 8))

        outer = ttk.Frame(self, style='Root.TFrame', padding=18)
        outer.pack(fill='both', expand=True)

        header = ttk.Frame(outer, style='Root.TFrame')
        header.pack(fill='x', pady=(0, 14))

        ttk.Label(header, text='HPLC / GC-MS Pipeline Launcher', style='Header.TLabel').pack(anchor='w')
        ttk.Label(
            header,
            text='Runs the pipeline as a desktop app with a live console log. Dummy mode is automated; real-data input stays console-driven.',
            style='Subtle.TLabel',
        ).pack(anchor='w', pady=(6, 0))

        content = ttk.Frame(outer, style='Root.TFrame')
        content.pack(fill='both', expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(1, weight=1)

        left = ttk.Frame(content, style='Card.TFrame', padding=16)
        left.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=(0, 10))

        right = ttk.Frame(content, style='Card.TFrame', padding=16)
        right.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=(10, 0))
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(left, text='Run Settings', style='CardTitle.TLabel').pack(anchor='w')
        ttk.Label(left, text='Choose a dummy-mode run profile for the packaged pipeline.', style='CardText.TLabel').pack(anchor='w', pady=(4, 14))

        mode_box = ttk.Frame(left, style='Card.TFrame')
        mode_box.pack(fill='x', pady=(0, 12))
        ttk.Label(mode_box, text='Data mode', style='CardText.TLabel').pack(anchor='w')
        ttk.Radiobutton(mode_box, text='Dummy data', value='dummy', variable=self.data_mode).pack(anchor='w', pady=(4, 0))
        ttk.Radiobutton(mode_box, text='Real data', value='real', variable=self.data_mode).pack(anchor='w')
        ttk.Label(mode_box, text='Real data mode is not automated in this launcher yet.', style='CardText.TLabel').pack(anchor='w', pady=(4, 0))

        source_box = ttk.Frame(left, style='Card.TFrame')
        source_box.pack(fill='x', pady=(0, 12))
        ttk.Label(source_box, text='Sources', style='CardText.TLabel').pack(anchor='w')
        ttk.Checkbutton(source_box, text='FTIR', variable=self.ftir).pack(anchor='w', pady=(4, 0))
        ttk.Checkbutton(source_box, text='HPLC', variable=self.hplc).pack(anchor='w')
        ttk.Checkbutton(source_box, text='GCMS', variable=self.gcms).pack(anchor='w')

        tune_box = ttk.Frame(left, style='Card.TFrame')
        tune_box.pack(fill='x', pady=(0, 12))
        ttk.Label(tune_box, text='Pipeline options', style='CardText.TLabel').pack(anchor='w')
        ttk.Checkbutton(tune_box, text='Skip DL model', variable=self.skip_dl).pack(anchor='w', pady=(4, 0))
        ttk.Checkbutton(tune_box, text='Validate species names', variable=self.validate_species).pack(anchor='w')

        numeric_box = ttk.Frame(left, style='Card.TFrame')
        numeric_box.pack(fill='x', pady=(0, 12))
        ttk.Label(numeric_box, text='Replicates', style='CardText.TLabel').grid(row=0, column=0, sticky='w', padx=(0, 8), pady=(0, 8))
        ttk.Entry(numeric_box, textvariable=self.reps, width=12).grid(row=0, column=1, sticky='w', pady=(0, 8))
        ttk.Label(numeric_box, text='Epochs', style='CardText.TLabel').grid(row=1, column=0, sticky='w', padx=(0, 8), pady=(0, 8))
        ttk.Entry(numeric_box, textvariable=self.epochs, width=12).grid(row=1, column=1, sticky='w', pady=(0, 8))
        ttk.Label(numeric_box, text='Batch size', style='CardText.TLabel').grid(row=2, column=0, sticky='w', padx=(0, 8))
        ttk.Entry(numeric_box, textvariable=self.batch_size, width=12).grid(row=2, column=1, sticky='w')

        button_row = ttk.Frame(left, style='Card.TFrame')
        button_row.pack(fill='x', pady=(6, 0))
        self.start_button = ttk.Button(button_row, text='Run pipeline', command=self._start_pipeline)
        self.start_button.pack(side='left')
        ttk.Button(button_row, text='Clear log', command=self._clear_log).pack(side='left', padx=(10, 0))

        status_row = ttk.Frame(left, style='Card.TFrame')
        status_row.pack(fill='x', pady=(16, 0))
        ttk.Label(status_row, text='Status', style='CardText.TLabel').pack(anchor='w')
        self.status_label = ttk.Label(status_row, text='Idle', style='CardText.TLabel')
        self.status_label.pack(anchor='w', pady=(4, 0))

        log_header = ttk.Frame(right, style='Card.TFrame')
        log_header.grid(row=0, column=0, sticky='ew')
        ttk.Label(log_header, text='Live Output', style='CardTitle.TLabel').pack(anchor='w')
        ttk.Label(log_header, text='This captures the console output from the pipeline run.', style='CardText.TLabel').pack(anchor='w', pady=(4, 12))

        self.log_text = scrolledtext.ScrolledText(
            right,
            wrap='word',
            height=30,
            bg='#081018',
            fg='#dbe7ff',
            insertbackground='#dbe7ff',
            relief='flat',
            padx=12,
            pady=12,
            font=('Consolas', 10),
        )
        self.log_text.grid(row=1, column=0, sticky='nsew')

        footer = ttk.Frame(right, style='Card.TFrame')
        footer.grid(row=2, column=0, sticky='ew', pady=(12, 0))
        ttk.Label(footer, text='The packaged exe will live in dist\\HPLC_GCMS_Pipeline\\HPLC_GCMS_Pipeline.exe after build.', style='CardText.TLabel').pack(anchor='w')

    def _clear_log(self) -> None:
        self.log_text.delete('1.0', 'end')

    def _append_log(self, text: str) -> None:
        self.log_text.insert('end', text)
        self.log_text.see('end')

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def _build_args(self) -> list[str]:
        args = [
            '--reps', self.reps.get().strip() or '15',
            '--epochs', self.epochs.get().strip() or '200',
            '--batch-size', self.batch_size.get().strip() or '16',
            '--skip-optimization',
        ]

        if self.skip_dl.get():
            args.append('--skip-dl')
        if self.validate_species.get():
            args.append('--validate-species')

        return args

    def _build_input_script(self) -> list[str]:
        if self.data_mode.get() != 'dummy':
            raise ValueError('This launcher currently automates dummy mode only.')

        sources = []
        if self.ftir.get():
            sources.append('1')
        if self.hplc.get():
            sources.append('2')
        if self.gcms.get():
            sources.append('3')

        if not sources:
            raise ValueError('Select at least one data source.')

        return ['1', ','.join(sources), 'n']

    def _start_pipeline(self) -> None:
        if self.pipeline_running:
            return

        try:
            input_script = self._build_input_script()
        except ValueError as exc:
            messagebox.showerror('Invalid selection', str(exc))
            return

        self.pipeline_running = True
        self.start_button.configure(state='disabled')
        self._set_status('Running')
        self._append_log('\n=== Starting pipeline ===\n')
        self._append_log(f'Working directory: {PROJECT_ROOT}\n')
        self._append_log(f'Arguments: {" ".join(self._build_args())}\n')
        self._append_log(f'Inputs: {input_script}\n\n')

        self.worker_thread = threading.Thread(
            target=self._run_pipeline_worker,
            args=(input_script,),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_pipeline_worker(self, scripted_inputs: list[str]) -> None:
        output_buffer = io.StringIO()
        prompts = iter(scripted_inputs)

        original_input = builtins.input
        original_argv = sys.argv[:]

        def scripted_input(prompt: str = '') -> str:
            if prompt:
                self.output_queue.put(prompt)
            try:
                answer = next(prompts)
            except StopIteration as exc:
                raise RuntimeError('The pipeline requested more input than the GUI provided.') from exc
            self.output_queue.put(f'{answer}\n')
            return answer

        try:
            builtins.input = scripted_input
            sys.argv = ['run_pipeline.py', *self._build_args()]
            with contextlib.redirect_stdout(QueueWriter(self.output_queue)), contextlib.redirect_stderr(QueueWriter(self.output_queue)):
                output_buffer.write('')
                run_pipeline.main()
            self.output_queue.put('\n=== Pipeline finished successfully ===\n')
            self.output_queue.put(('status', 'Finished'))
        except SystemExit as exc:
            self.output_queue.put(f'\n=== Pipeline exited with code {exc.code} ===\n')
            self.output_queue.put(('status', f'Exited: {exc.code}'))
        except Exception:
            self.output_queue.put('\n=== Pipeline failed ===\n')
            self.output_queue.put(traceback.format_exc())
            self.output_queue.put(('status', 'Failed'))
        finally:
            builtins.input = original_input
            sys.argv = original_argv
            self.output_queue.put(('done', ''))

    def _poll_queue(self) -> None:
        try:
            while True:
                item = self.output_queue.get_nowait()
                if isinstance(item, tuple):
                    tag, value = item
                    if tag == 'status':
                        self._set_status(value)
                    elif tag == 'done':
                        self.pipeline_running = False
                        self.start_button.configure(state='normal')
                    continue
                self._append_log(item)
        except queue.Empty:
            pass
        self.after(60, self._poll_queue)


def main() -> None:
    app = PipelineGui()
    app.mainloop()


if __name__ == '__main__':
    main()