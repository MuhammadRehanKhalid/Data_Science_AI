from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Include torch dynamic libs (shared libraries) and data files
try:
    binaries = collect_dynamic_libs("torch")
except Exception:
    binaries = []

try:
    datas = collect_data_files("torch")
except Exception:
    datas = []

# Some torch internals are imported dynamically; keep these as explicit hiddenimports
hiddenimports = [
    "torch._C",
    "torch._dynamo",
]
