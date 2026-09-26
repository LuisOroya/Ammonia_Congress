# Repository cleanup and execution changes

## Current revision

- Added independent top-level runners for Stage 0, Stage 1, Stage 2, and Stage 3.
- Added Windows `.bat` launchers for the same stage-specific workflows.
- Added `--validate-only` to the Stage-2 runner so existing Stage-2 outputs can be audited without rerunning AMPL.
- Updated the Stage-2 N/M ordering audit:
  - `1e-5 < V_N - V_M <= 1e-3`: numerical warning;
  - `V_N - V_M > 1e-3`: fatal validation error.
- Documented the S5 diagnostic showing that the small N/M inversion is a Stage-B MILP solver-path effect.
- Removed `option presolve_eps 1e-10;` from the S5 diagnostic; its removal did not change the diagnostic result.
- Preserved the original two-level Stage-2 formulation: Stage A minimizes operating cost and Stage B minimizes variability under the cost lock.
- The full `run_pipeline.py` remains available for deliberate end-to-end reruns.
