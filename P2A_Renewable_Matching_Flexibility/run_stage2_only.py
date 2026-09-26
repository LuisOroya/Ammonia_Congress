#!/usr/bin/env python3
"""Run or validate only Stage 2 without launching Stage 1 or Stage 3."""
from pathlib import Path
import argparse, subprocess, sys

ROOT = Path(__file__).resolve().parent

def run(args):
    print("\\n>>>", " ".join(map(str,args)))
    subprocess.run(args, cwd=ROOT, check=True)

def main():
    ap=argparse.ArgumentParser(description="Run only Stage 2 baseline operation.")
    ap.add_argument("--overwrite", action="store_true",
                    help="Delete/replace current Stage-2 outputs and solve again.")
    ap.add_argument("--validate-only", action="store_true",
                    help="Audit existing Stage-2 outputs without solving AMPL again.")
    a=ap.parse_args()

    cmd=[sys.executable, "02_stage2_baselines/run_stage2.py"]
    if a.overwrite:
        cmd.append("--overwrite")
    if a.validate_only:
        cmd.append("--validate-only")
    run(cmd)
    print("\\nStage 2 finished successfully. No Stage 1/3 job was started.")

if __name__ == "__main__":
    main()
