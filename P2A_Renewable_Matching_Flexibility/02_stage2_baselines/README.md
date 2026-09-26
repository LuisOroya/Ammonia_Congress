# Stage 2 — Matching-specific baseline operation

Stage 2 uses the freshly generated K=9 Stage-1 reference design and solves each `(scenario, matching regime)` independently.

Regimes:
- `NO_MATCH`
- `MONTHLY`
- `HOURLY`

For every pair, Stage A minimizes grid-related operating cost. Stage B then minimizes normalized variation of electrolyzer power and ammonia production subject to a cost allowance of 0.01 USD above Stage A.

Run:

```powershell
py 02_stage2_baselines/run_stage2.py --overwrite
```

The runner refuses to start if the selected Stage-1 result is missing. A post-run validator checks output completeness, the Stage-B cost lock, power balance, and the expected N/M secondary-objective ordering when their primary optima coincide. A documented S5 diagnostic showed that a very small ordering inversion (about $10^{-4}$ in the normalized objective) can arise from the Stage-B MILP solution path even with zero requested MIP gap. Such small discrepancies are reported as numerical warnings; material inversions above $10^{-3}$ remain fatal.


## PEM/PWL input

This stage does not contain its own breakpoint table. The runner copies the centralized PEM/PWL file `00_pem_curve/generated/pem_pwl_6segments.dat` into the temporary AMPL work directory. Regenerate that file with `py 00_pem_curve/generate_pem_pwl.py` if the nonlinear PEM assumptions or segment count are changed.


To validate already generated Stage-2 outputs without resolving the optimization:

```powershell
py run_stage2_only.py --validate-only
```

To resolve only Stage 2 from the repository root:

```powershell
py run_stage2_only.py --overwrite
```
