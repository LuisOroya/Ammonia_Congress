#!/usr/bin/env python3
"""Run only Stage 0: nonlinear PEM preprocessing -> 6-segment PWL artifact."""
from pathlib import Path
import argparse, subprocess, sys

ROOT = Path(__file__).resolve().parent

def run(args):
    print("\\n>>>", " ".join(map(str,args)))
    subprocess.run(args, cwd=ROOT, check=True)

def main():
    ap=argparse.ArgumentParser(description="Run only PEM/PWL preprocessing (Stage 0).")
    ap.add_argument("--segments", type=int, default=6)
    a=ap.parse_args()
    run([sys.executable, "00_pem_curve/generate_pem_pwl.py", "--segments", str(a.segments)])
    run([sys.executable, "validate_repository.py"])
    print("\\nStage 0 finished successfully.")

if __name__ == "__main__":
    main()
