import argparse
import subprocess
from pathlib import Path


def run(cmd: list):
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venv", default=".venv")
    ap.add_argument("--data", default="Algae_Antioxidant_Project/data/algae_antioxidants_dummy.csv")
    ap.add_argument("--projroot", default="Algae_Antioxidant_Project")
    args = ap.parse_args()

    proj = Path(args.projroot)
    data_path = Path(args.data)

    if not data_path.exists():
        run(["python", str(proj / "src" / "generate_dummy_data.py"), "--out", str(data_path)])

    run(["python", str(proj / "src" / "analysis_basic.py"), "--data", str(data_path), "--outdir", str(proj / "reports"), "--plots", str(proj / "plots")])
    run(["python", str(proj / "src" / "modeling_ml.py"), "--data", str(data_path), "--outdir", str(proj / "reports"), "--plots", str(proj / "plots")])
    run(["python", str(proj / "src" / "modeling_dl.py"), "--data", str(data_path), "--outdir", str(proj / "reports"), "--plots", str(proj / "plots")])
    print("All steps completed.")


if __name__ == "__main__":
    main()
