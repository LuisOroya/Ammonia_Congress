# Stage 1 — Reference sizing

The same P2A planning model is solved for the supplied K=5,...,15 representative monthly scenario sets. PV, wind, and H2-storage capacities are endogenous; conversion-process capacities are fixed. Hourly matching applies to PEM stack + BOP.

Run all K values from the repository root with:

```powershell
py 01_stage1_reference_sizing/run_stage1.py --overwrite
```

Or K=9 only:

```powershell
py 01_stage1_reference_sizing/run_stage1.py --selected-only --overwrite
```

Each solve is executed in a temporary directory, so source inputs are never overwritten. Full solver output is preserved in `results/stage1/Kxx/solver_log.txt`.

The AMPL run requests a relative MIP gap of `1e-4` (0.01%) and a 7200-s time limit. The Python runner creates `reference_design_rounded.dat` from the exact printed optimum using conservative upward rounding of 0.001 MW for PV/wind and 1 kg for H2 storage.


## PEM/PWL input

This stage does not contain its own breakpoint table. The runner copies the centralized PEM/PWL file `00_pem_curve/generated/pem_pwl_6segments.dat` into the temporary AMPL work directory. Regenerate that file with `py 00_pem_curve/generate_pem_pwl.py` if the nonlinear PEM assumptions or segment count are changed.
