# Numerical reproducibility notes

## Stage-2 hierarchical cost lock

During cleanup, an S4 diagnostic exposed a numerical sensitivity in the earlier Stage-2 secondary objective. The development version used an absolute Stage-B allowance of `0.001 USD` above the Stage-A optimum.

For S4 monthly matching, an archived binary segment pattern was physically feasible and reproduced the archived variability objective when given a safely feasible cost limit, but its minimum exact operating cost under the current solver realization exceeded the original Stage-B lock by only approximately `1.5232e-4 USD`.

This is not a physical effect of monthly matching. It is a solver/numerical-path issue caused by using an economically meaningless sub-cent cost allowance on a monthly problem with costs on the order of tens of thousands of dollars.

The clean repository therefore uses:

```text
COST_LOCK_EPS = 0.01 USD per independently solved scenario
```

This is still negligible economically (about 2.2e-7 of the S4 Stage-A cost) while providing a more reproducible hierarchical tie-breaker. Because this changes a computational setting, **all Stage-2 and Stage-3 outputs must be regenerated** before final publication; no pre-clean Stage-2/3 results are treated as authoritative in this repository.

## Solver settings

- Stage 1: Gurobi `mipgap=1e-4`, `mipfocus=2`, `presolve=2`, 16 threads, 7200-s time limit.
- Stage 2: Gurobi `mipgap=0`, `mipfocus=2`, `presolve=2`, 16 threads.
- Stage 3: Gurobi `mipgap=0`, `mipfocus=2`, `presolve=2`, 16 threads.

The solver logs are part of the reproducibility record. A requested zero relative gap should not be described as proof that every solve has zero absolute numerical gap; preserve logs for exact solver messages and bounds.


## S5 N/M secondary-objective diagnostic

With the `0.01 USD` Stage-B cost allowance, scenario S5 returned a small fresh-solve ordering inversion:

```text
V_N(fresh) = 2.0551166836
V_M        = 2.0550176675
```

The Stage-A costs were both exactly zero and the common Stage-B ceiling was `0.01 USD`. A dedicated diagnostic then replayed the MONTHLY PWL segment pattern inside the less-constrained NO_MATCH problem. It obtained:

```text
V_N(fixed-M) = 2.0550074535
V_N(warm)    = 2.0550074535
```

with a MONTHLY renewable-matching margin of approximately `3780.8683 MWh`. Removing `option presolve_eps 1e-10;` from the diagnostic did not change any of these values.

This proves that the small fresh-solve inversion is a solver-path/numerical effect in the Stage-B MILP, not a physical benefit created by monthly matching. The validator therefore:

- issues a warning for `1e-5 < V_N - V_M <= 1e-3` when the Stage-A costs coincide;
- still stops for a material inversion `V_N - V_M > 1e-3`.

The mathematical Stage-2 formulation is unchanged: Stage A minimizes operating cost and Stage B minimizes process variability under the cost lock. No additional optimization level is introduced.
