#!/usr/bin/env python3
"""Run only Stage 1 without automatically launching downstream stages."""
from pathlib import Path
import argparse, subprocess, sys

ROOT = Path(__file__).resolve().parent

def run(args):
    print("\\n>>>", " ".join(map(str,args)))
    subprocess.run(args, cwd=ROOT, check=True)

def main():
    ap=argparse.ArgumentParser(description="Run only Stage 1 reference sizing.")
    ap.add_argument("--mode", choices=("selected","sweep"), default="selected",
                    help="selected = K=9 only (default); sweep = K=5..15.")
    ap.add_argument("--k", type=int, help="Run one specific configured K instead of --mode.")
    ap.add_argument("--overwrite", action="store_true")
    a=ap.parse_args()

    cmd=[sys.executable, "01_stage1_reference_sizing/run_stage1.py"]
    if a.overwrite:
        cmd.append("--overwrite")
    if a.k is not None:
        cmd += ["--k", str(a.k)]
    elif a.mode == "selected":
        cmd.append("--selected-only")
    run(cmd)

    if a.k is None and a.mode == "sweep":
        run([sys.executable, "01_stage1_reference_sizing/analyze_stage1_sweep.py"])
    print("\\nStage 1 finished successfully. No Stage 2/3 job was started.")

if __name__ == "__main__":
    main()
