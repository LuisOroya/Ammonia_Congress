# Renewable-Matching Effects on Power-to-Ammonia Operational Flexibility

Reproducibility repository for the PEM preprocessing and three-stage optimization workflow used to study how temporal renewable matching changes the sustained operational flexibility of a grid-connected power-to-ammonia (P2A) plant.

## Reproducibility scope

The repository contains two linked computational layers:

0. **PEM preprocessing — nonlinear curve to PWL model.** Rebuild the nonlinear PEM hydrogen-production curve, evaluate alternative segmentation levels, and recover the six-segment dynamic-programming PWL coefficients used by all optimization stages.
1. **Stage 1 — reference sizing.** Optimize PV, wind, and H2-storage capacity for each supplied K=5,...,15 representative scenario set under hourly renewable matching.
2. **Stage 2 — baseline operation.** Fix the selected K=9 design and compute no-matching, monthly-matching, and hourly-matching baselines through hierarchical optimization.
3. **Stage 3 — paired flexibility.** Compare physical (`PHYS`) and renewable-matching-compliant (`RM`) sustained load flexibility for INC/DEC activations of 1, 4, 12, and 24 h.

The raw weather archive and the code that originally generated the K-medoids scenario sets are not contained in the supplied project package. Therefore the repository reproduces the PEM/PWL preprocessing and Stages 1–3 **conditional on the supplied representative scenario sets**. See `docs/DATA_PROVENANCE.md`.

## PEM/PWL preprocessing

The supplied PEM notebook is preserved in `00_pem_curve/notebooks/`, while `00_pem_curve/generate_pem_pwl.py` is the authoritative scripted implementation used for reproducibility.

The preprocessing uses:

- a 94.7 MW PEM stack at 60 °C and 30 bar on both electrodes;
- productive normalized power range `[0.15, 1.00]`;
- a 50,000-point dense grid to invert the monotone current-density/power relation;
- exactly 1,000 uniformly spaced candidate points in normalized power;
- endpoint-interpolating chord SSE for each candidate segment;
- dynamic programming to find the globally minimum-SSE breakpoint subset for a fixed number of segments within that candidate grid.

The final study configuration uses **six segments**:

`[0.15000, 0.26401, 0.38909, 0.52523, 0.67242, 0.83068, 1.00000]`.

Its master-grid RMSE is approximately `0.01169755 kg/MWh` (`0.063452%` of rated normalized production), with maximum absolute error approximately `0.01783739 kg/MWh` (`0.096756%`). The script also reports 3-, 5-, 9-, 12-, and 15-segment alternatives. The choice of six segments is a fixed fidelity/complexity modeling decision, not an automatically selected segment count.

Stages 1–3 all load the same generated file:

`00_pem_curve/generated/pem_pwl_6segments.dat`

so the PWL coefficients are not duplicated across stage-specific data files.

## Requirements

- Python 3.11+
- AMPL available on `PATH`
- Gurobi available through AMPL with a valid license (the clean rerun targets Gurobi 13.0.x)
- Python packages in `requirements.txt`

Windows PowerShell:

```powershell
py -m pip install -r requirements.txt
ampl -v
py validate_repository.py
```

## Recommended clean rerun for the paper

The intended paper rerun starts at Stage 1 while using the already generated and validated six-segment PEM file:

```powershell
py run_pipeline.py --fresh --from-stage 1 --stage1-mode sweep
```

This executes

`Stage 1 K=5...15 -> Stage 2 K=9 -> Stage-3 pilot -> full Stage 3 -> paper post-processing`.

For a completely end-to-end regeneration beginning with the nonlinear PEM model:

```powershell
py run_pipeline.py --fresh --from-stage 0 --stage1-mode sweep
```

Stage 0 first rebuilds the nonlinear PEM curve and `pem_pwl_6segments.dat`, validates the repository, and then starts Stage 1.

For a faster downstream-only rerun after a complete K sweep exists:

```powershell
py run_pipeline.py --from-stage 2
```

For a K=9-only Stage-1 check (this does **not** reproduce the K-sweep stability analysis):

```powershell
py run_pipeline.py --fresh --from-stage 1 --stage1-mode selected
```

## Run individual stages

Each computational stage now has a top-level launcher. These commands **do not run earlier stages automatically**; they use already available upstream outputs and stop if a required dependency is missing.

```powershell
# Stage 0 only: rebuild nonlinear PEM curve and PWL coefficients
py run_stage0_only.py

# Stage 1 only: K=9 by default
py run_stage1_only.py --overwrite

# Full K=5,...,15 Stage-1 sweep only
py run_stage1_only.py --mode sweep --overwrite

# Stage 2 only: use existing selected-K Stage-1 design
py run_stage2_only.py --overwrite

# Validate the Stage-2 files already on disk, without resolving AMPL
py run_stage2_only.py --validate-only

# Stage 3 only: use existing Stage-1/Stage-2 outputs
py run_stage3_only.py --overwrite

# Stage-3 pilot only
py run_stage3_only.py --overwrite --pilot-only
```

On Windows, equivalent launchers are provided at the repository root:

`RUN_STAGE0_PEM.bat`, `RUN_STAGE1.bat`, `RUN_STAGE2.bat`, and `RUN_STAGE3.bat`.

They forward optional arguments. For example:

```powershell
RUN_STAGE2.bat --validate-only
RUN_STAGE3.bat --overwrite --pilot-only
```

The original `run_pipeline.py` remains available for deliberate end-to-end runs.

## Expected outputs

### Stage 0

```text
00_pem_curve/generated/
    pem_master_curve.csv
    pem_pwl_metrics.csv
    pem_pwl_coefficients_all.csv
    pem_pwl_6segments.dat
    pem_pwl_summary.json
```

### Stage 1

```text
results/stage1/K05 ... K15/
    planning_summary.csv
    planning_scenario_summary.csv
    planning_dispatch.csv
    planned_capacities_exact.dat
    reference_design_rounded.dat
    solver_log.txt
    manifest.json
results/stage1/stage1_sweep_summary.csv
```

The selected scenario set is K=9. Downstream conservative rounding is implemented once in Python: PV/wind upward to 0.001 MW and H2 storage upward to 1 kg.

### Stage 2

```text
results/stage2/
    stage2_case_summary.csv
    stage2_case_scenario_summary.csv
    stage2_scenario_solve_summary.csv
    stage2_baselines.csv
    stage2_segments.csv
    stage2_reference_design.csv
    solver_log.txt
    manifest.json
```

Stage A minimizes grid-related operating cost. Stage B minimizes normalized hour-to-hour process variation while allowing at most **0.01 USD** above the Stage-A optimum. The earlier development workflow used 0.001 USD; an S4 diagnostic showed this was unnecessarily close to solver-level numerical noise. See `docs/NUMERICAL_NOTES.md`.

### Stage 3

The official Stage-3 runner first executes a 64-row pilot and validates nesting before launching the full sweep.

```text
results/stage3/
    stage3_baselines_k09.dat
    stage3_pilot_results.csv
    pilot_stage3_*.csv
    stage3_flexibility_results.csv
    stage3_scenario_summary.csv
    stage3_retention_summary.csv
    pilot_solver_log.txt
    full_solver_log.txt
    manifest.json
```

For the current K=9 scenario durations and structured activation sampling, the full run must contain **2,864 paired event rows**. The analyzer checks that no material event satisfies `F_RM > F_PHYS + 0.001 MW`.

## Repository structure

```text
00_pem_curve/                  Nonlinear PEM model, DP breakpoint generation, central PWL data
01_stage1_reference_sizing/    Stage-1 model, parameters, scenario sets, runner
02_stage2_baselines/           Stage-2 model, parameters, runner, validation
03_stage3_flexibility/         Stage-3 model, preparation, pilot/full runs, analysis
scripts/                       Reproducibility utilities
results/                       Generated optimization outputs only
docs/                          Data, numerical, model-scope, and release notes
```

## Important modeling boundaries

- Renewable matching applies to **PEM stack + BOP**, not every P2A auxiliary load.
- Stage-3 flexibility is a sustained deviation of **gross P2A electrical demand**, not a certified net-grid reserve product.
- Recovery is allowed over the remaining representative month, while the ammonia-production commitment and terminal H2 inventory are retained.
- Stage 3 uses monthly and hourly baselines; no-matching has no distinct RM branch.
- The electrochemical PEM model is used only to construct the PWL conversion curve; the optimization itself uses the exact segment-binary PWL representation.

## Reproducibility discipline

- Do not hand-edit files under `results/`.
- Do not hand-edit `00_pem_curve/generated/pem_pwl_6segments.dat`; regenerate it with `generate_pem_pwl.py`.
- Do not copy Stage-1 design numbers into Stage-2/3 source files; downstream runners load the selected Stage-1 result directly.
- Preserve solver logs and `manifest.json` files with final published results.
- Commit final result files only after the clean Stage-1 -> Stage-2 -> Stage-3 rerun is complete and validated.

## Public-release checklist

Before making the repository public, add the final manuscript citation/DOI, choose explicit software/data licenses, and complete the scenario-reduction provenance described in `docs/DATA_PROVENANCE.md`.
