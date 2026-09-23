from pathlib import Path
import shutil
import subprocess
import sys


# ============================================================
# STAGE-1 SCENARIO SWEEP
# Runs K = 5,...,15
#
# Usage:
#
# py run_stage1_sweep.py "..\11_Clean_Version\01_Stage1_ReferenceSizing"
#
# The script must be located beside:
#
#   K05\
#   K06\
#   ...
#   K15\
#
# Each Kxx folder must contain:
#
#   planning_scenarios_2025.dat
#   planning_profiles_2025.dat
#
# ============================================================


# ------------------------------------------------------------
# 1. INPUT FOLDERS
# ------------------------------------------------------------

# Folder containing this Python script.
ROOT = Path(__file__).resolve().parent

# Stage-1 AMPL working folder.
#
# If a path is supplied in the command line, use it.
# Otherwise, use the current working directory.
if len(sys.argv) >= 2:
    STAGE1 = Path(sys.argv[1]).expanduser().resolve()
else:
    STAGE1 = Path.cwd().resolve()


AMPL_RUN = "main_planning_2025.run"


# ------------------------------------------------------------
# 2. CHECK REQUIRED STAGE-1 FILES
# ------------------------------------------------------------

required_stage1_files = [
    "p2a_planning_scenarios.mod",
    AMPL_RUN,
]

missing = [
    name
    for name in required_stage1_files
    if not (STAGE1 / name).exists()
]

if missing:
    raise SystemExit(
        "\n"
        "============================================================\n"
        "ERROR: Stage-1 folder is not correct.\n"
        "============================================================\n"
        f"Folder checked:\n{STAGE1}\n\n"
        "Missing files:\n"
        + "\n".join(f"  - {name}" for name in missing)
        + "\n\n"
        "Example usage:\n"
        'py run_stage1_sweep.py '
        '"..\\11_Clean_Version\\01_Stage1_ReferenceSizing"\n'
    )


# ------------------------------------------------------------
# 3. CHECK K-SCENARIO FOLDERS
# ------------------------------------------------------------

for k in range(5, 16):

    tag = f"K{k:02d}"
    source = ROOT / tag

    required_k_files = [
        "planning_scenarios_2025.dat",
        "planning_profiles_2025.dat",
    ]

    if not source.exists():
        raise SystemExit(
            f"\nERROR: Scenario folder not found:\n{source}\n"
        )

    missing_k = [
        name
        for name in required_k_files
        if not (source / name).exists()
    ]

    if missing_k:
        raise SystemExit(
            f"\nERROR: Missing files in {tag}:\n"
            + "\n".join(f"  - {name}" for name in missing_k)
            + "\n"
        )


# ------------------------------------------------------------
# 4. RESULT FOLDER
# ------------------------------------------------------------

results_root = STAGE1 / "K_sweep_results"
results_root.mkdir(exist_ok=True)


# Stage-1 outputs that will be copied after each solve.
output_files = [
    "planning_summary.csv",
    "planning_scenario_summary.csv",
    "planning_dispatch.csv",
    "planned_capacities_exact.dat",
    "reference_design_rounded.dat",
]


# ------------------------------------------------------------
# 5. RUN K = 5,...,15
# ------------------------------------------------------------

for k in range(5, 16):

    tag = f"K{k:02d}"
    source = ROOT / tag

    print("\n")
    print("=" * 60)
    print(f"Running {tag}")
    print("=" * 60)
    print(f"Scenario source : {source}")
    print(f"AMPL work folder: {STAGE1}")
    print("=" * 60)
    print()


    # --------------------------------------------------------
    # 5.1 Copy scenario data into Stage-1 folder
    # --------------------------------------------------------

    shutil.copy2(
        source / "planning_scenarios_2025.dat",
        STAGE1 / "planning_scenarios_2025.dat",
    )

    shutil.copy2(
        source / "planning_profiles_2025.dat",
        STAGE1 / "planning_profiles_2025.dat",
    )


    # --------------------------------------------------------
    # 5.2 Create result folder for this K
    # --------------------------------------------------------

    dest = results_root / tag
    dest.mkdir(exist_ok=True)


    # --------------------------------------------------------
    # 5.3 Run AMPL with LIVE console output
    # --------------------------------------------------------

    process = subprocess.Popen(
        ["ampl", AMPL_RUN],
        cwd=STAGE1,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    )


    # Save all AMPL/Gurobi output while also showing it live.
    log_lines = []

    for line in process.stdout:

        # Show line immediately in PowerShell.
        print(line, end="", flush=True)

        # Store line for solver_log.txt.
        log_lines.append(line)


    returncode = process.wait()


    # --------------------------------------------------------
    # 5.4 Save complete solver log
    # --------------------------------------------------------

    log_path = dest / "solver_log.txt"

    log_path.write_text(
        "".join(log_lines),
        encoding="utf-8",
    )


    # --------------------------------------------------------
    # 5.5 Check solver execution
    # --------------------------------------------------------

    if returncode != 0:

        print("\n")
        print("=" * 60)
        print(f"ERROR: {tag} FAILED")
        print("=" * 60)
        print(f"See solver log:\n{log_path}")
        print("=" * 60)

        raise SystemExit(returncode)


    # --------------------------------------------------------
    # 5.6 Copy Stage-1 results
    # --------------------------------------------------------

    for name in output_files:

        src = STAGE1 / name

        if src.exists():

            shutil.copy2(
                src,
                dest / name,
            )

        else:

            print(
                f"WARNING: Expected output not found: {name}"
            )


    # --------------------------------------------------------
    # 5.7 Save exact scenario inputs used
    # --------------------------------------------------------

    shutil.copy2(
        source / "planning_scenarios_2025.dat",
        dest / "planning_scenarios_2025.dat",
    )

    shutil.copy2(
        source / "planning_profiles_2025.dat",
        dest / "planning_profiles_2025.dat",
    )


    print()
    print("=" * 60)
    print(f"{tag} COMPLETED")
    print("=" * 60)
    print(f"Results saved in:")
    print(dest)
    print("=" * 60)


# ------------------------------------------------------------
# 6. FINISH
# ------------------------------------------------------------

print("\n")
print("=" * 60)
print("STAGE-1 K SWEEP COMPLETE")
print("=" * 60)
print("Solved:")
print("K = 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15")
print()
print("All results saved in:")
print(results_root)
print("=" * 60)