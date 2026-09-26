# Stage 3 — Paired PHYS/RM flexibility

Stage 3 uses the freshly generated monthly and hourly Stage-2 baselines.

For each activation event:
- `PHYS`: matching is relaxed from activation onward.
- `RM`: the baseline matching regime is retained.

The comparison preserves the same pre-activation history/state, design, ammonia-production commitment, and terminal H2-inventory requirement.

Directions: INC and DEC. Durations: 1, 4, 12, and 24 h.

Full-sweep starts use within-day indices `{1, 7, 13, 19}` every 7 days. These are index positions spaced by six hours; the wall-clock label depends on the timestamp convention of the source data.

Run:

```powershell
py 03_stage3_flexibility/run_stage3.py --overwrite
```

The runner generates Stage-3 baseline data directly from the fresh Stage-2 CSV, validates the reference design, runs a 64-row S4 pilot, checks nesting, and only then launches the full 2,864-row paired-event sweep.


## PEM/PWL input

This stage does not contain its own breakpoint table. The runner copies the centralized PEM/PWL file `00_pem_curve/generated/pem_pwl_6segments.dat` into the temporary AMPL work directory. Regenerate that file with `py 00_pem_curve/generate_pem_pwl.py` if the nonlinear PEM assumptions or segment count are changed.
