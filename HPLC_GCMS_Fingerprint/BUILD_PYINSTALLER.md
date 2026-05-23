# Building a Windows executable with PyInstaller

This document shows a starting point for packaging `run_pipeline.py` as a Windows distributable using PyInstaller.

Prerequisites
- A working Python 3.10 environment (same architecture you intend to run on)
- Install build dependencies in a venv: `pip install -r requirements.txt pyinstaller`
- On Windows, install the Visual C++ Redistributable that matches your Python build.

Quick test (recommended: `--onedir` for debugging)

```powershell
cd HPLC_GCMS_Fingerprint
pyinstaller --clean --noconfirm --additional-hooks-dir=hooks run_pipeline.spec
```

Notes and next steps
- If you see runtime errors about a missing `python310.dll`, rebuild using the same Python installation or switch to a clean virtualenv.
- Use `--onedir` first to inspect the `dist/run_pipeline` folder and confirm `python310.dll` and package DLLs are present.
- If specific modules are missing at runtime, add them to the `hiddenimports` list in the `.spec` or create a hook `hook-<module>.py` in `hooks/`.
- For `numpy`, `scipy`, `torch`, and `pandas` you may need to collect data/binaries manually; the `run_pipeline.spec` attempts to collect common files but you should iterate based on runtime logs.
- To produce a single-file `--onefile` exe, switch `COLLECT`/`EXE` options in the spec or run `pyinstaller --onefile run_pipeline.spec` (expect longer startup time).

Auto-update and distribution
- For future updates, rebuild the exe and publish via GitHub Releases or an internal file server.
- Optionally implement an in-app updater that checks a version API and downloads the new installer.
