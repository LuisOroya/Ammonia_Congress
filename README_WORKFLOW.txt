P2A REFERENCE-DESIGN -> BASELINE -> FLEXIBILITY WORKFLOW
=======================================================
Exact SB-PWL version. No RB-PWL relaxation is used.

Folder 01 - Stage 1: Reference sizing
------------------------------------
Purpose: obtain a defensible reference RES/H2-buffer design for a FIXED P2A
conversion plant. Stage 1 is supporting methodology, not the paper's main
planning contribution.

Current provisional 2025 Stage-1 numerical optimum:
  PV       ~ 78.674440 MW
  Wind     ~ 407.514020 MW
  H2 tank  ~ 48175.609558 kg

For downstream operational studies the design is conservatively rounded UP:
  PV       = 78.68 MW
  Wind     = 407.52 MW
  H2 tank  = 48180 kg = 48.18 t

The Stage-1 run writes both:
  planned_capacities_exact.dat       (traceability)
  reference_design_rounded.dat       (used downstream)

Rounding rule:
  PV/wind: upward to 0.01 MW
  H2 tank: upward to 10 kg

Run:
  include main_planning_2025.run;

If Stage 1 is rerun, return to the ZIP root and run:
  python sync_reference_design.py
This copies the NEW rounded values into Stage 2 and Stage 3 common-data files.

Folder 02 - Stage 2: Operational baselines
------------------------------------------
Purpose: with the rounded reference design fixed, compute C0 / monthly /
weekly / hourly exact SB-PWL baselines.

Run:
  include main_stage2_2025_baselines_sbpwl.run;

Important outputs for Stage 3:
  stage2_baselines.csv
  stage2_reference_design.csv

Do NOT use Stage-2 baselines generated with different capacities.
If the reference design changes, Stage 2 MUST be rerun.

Folder 03 - Stage 3: Paired flexibility
---------------------------------------
Purpose: exact SB-PWL PHYS-vs-RM activation assessment using compressed
pre-activation history (H2 state, prior NH3 production, and matching-accounting
history), rather than point-by-point fixing of redundant rounded variables.

After Stage 2 finishes, from folder 03 run:
  python prepare_stage3_baselines.py

The script verifies that Stage-2 and Stage-3 capacities are IDENTICAL and then
creates:
  flex_baselines_2025.dat

Then run ONLY the smoke test first:
  include main_flex_smoke.run;

If clean:
  include main_flex_pilot_24h.run;

Only after inspection:
  include main_flex_dev_6h.run;

Critical checks:
  - no infeasible smoke cases;
  - rm_gt_phys_count = 0 in every summary row;
  - near-zero DeltaP values must not be interpreted when solver violations are
    of comparable/larger magnitude;
  - renewable matching is NOT relaxed by a policy-side tolerance.

CURRENT DEVELOPMENT STATUS
--------------------------
This package still uses the provisional 12 calendar months of 2025 for Stage 1
and development scenarios March/September for Stage 3. Once the final
2016-2025 representative scenarios and weights are available, replace the
scenario/profile inputs, rerun Stage 1, synchronize the rounded design, rerun
Stage 2, and regenerate Stage-3 baselines.

Scientific interpretation
-------------------------
Stage 1 only establishes a normal-operating reference installation. The fixed
P2A conversion train is not optimized. The main paper question remains how
much physical P2A load flexibility is retained under temporal renewable
matching.
