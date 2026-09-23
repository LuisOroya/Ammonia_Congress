STAGE 2 - MATCHING-SPECIFIC FIXED-DESIGN BASELINES
===================================================
Selected scenario set: K=9 representative months.
Fixed conservative upward-rounded Stage-1 reference design:
  PV       = 159.96 MW
  Wind     = 499.30 MW
  H2 tank  = 27920 kg

Matching cases:
  C0 = no matching
  C1 = monthly matching
  C2 = hourly matching

FINAL computational structure
-----------------------------
Every (scenario s, matching case c) is solved independently.
Therefore Stage 2 performs:
  9 scenarios x 3 matching cases x 2 lexicographic levels = 54 solves.

This is mathematically consistent with the paper formulation, which defines a
baseline for each (s,c), and avoids one large MILP containing all nine months.
Scenario probabilities are NOT part of an individual baseline optimization;
they are used only after the independent solves to compute case-level expected
summary quantities.

Baseline selection for EACH (s,c)
---------------------------------
  Stage A = minimum grid-related operating cost
  Stage B = minimum normalized process variability with that scenario's
            Stage-A cost locked within COST_LOCK_EPS

Stage-B variability metric:
  total variation of
    |Delta P_EL| / P_EL_MAX + |Delta NH3| / Q_NH3_MAX
  over consecutive hours of the active representative month.

This tie-breaker is used because economic baselines, especially under monthly
matching, can be non-unique. It preserves the economic optimum within
COST_LOCK_EPS while selecting a smoother representative operating trajectory.

Final solver environment for the paper workflow:
  Gurobi 13.0.3
  mipgap=0.001, mipfocus=2, presolve=2, threads=16

Run in AMPL:
  include main_stage2_2025_baselines_sbpwl.run;

Outputs:
  stage2_case_summary.csv
  stage2_case_scenario_summary.csv
  stage2_scenario_solve_summary.csv
  stage2_baselines.csv
  stage2_segments.csv
  stage2_reference_design.csv

Expected computational benefit:
  Each MILP contains only one representative month rather than all K=9 months,
  so the exact SB-PWL binaries are separated across independent solves. This
  should materially reduce branch-and-bound difficulty, especially for the
  Stage-B variability tie-breaker.

Recommended validation before Stage 3:
  Run Stage 2 twice with unchanged files/settings and compare
  stage2_baselines.csv. Small numerical-tolerance differences are acceptable;
  material trajectory changes should be investigated before freezing Stage 3.
