#!/usr/bin/env python3
"""Run only Stage 3 using existing Stage-1 and Stage-2 results."""
from pathlib import Path
import argparse, subprocess, sys

ROOT = Path(__file__).resolve().parent

def run(args):
    print("\\n>>>", " ".join(map(str,args)))
    subprocess.run(args, cwd=ROOT, check=True)

def main():
    ap=argparse.ArgumentParser(description="Run only Stage 3 paired flexibility.")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--pilot-only", action="store_true")
    ap.add_argument("--skip-postprocess", action="store_true",
                    help="Do not rebuild the compact paper-result summary after a full run.")
    a=ap.parse_args()

    cmd=[sys.executable, "03_stage3_flexibility/run_stage3.py"]
    if a.overwrite:
        cmd.append("--overwrite")
    if a.pilot_only:
        cmd.append("--pilot-only")
    run(cmd)

    if not a.pilot_only and not a.skip_postprocess:
        run([sys.executable, "postprocess_paper_results.py"])
    print("\\nStage 3 finished successfully. No upstream stage was rerun.")

if __name__ == "__main__":
    main()
