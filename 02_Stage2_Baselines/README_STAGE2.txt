STAGE 2 - FIXED-DESIGN BASELINES
===============================
Uses the conservative upward-rounded Stage-1 reference design:
PV=78.68 MW, wind=407.52 MW, H2 tank=48180 kg (until Stage 1 is rerun).

Run: include main_stage2_2025_baselines_sbpwl.run;

Generates C0, monthly, weekly and hourly exact SB-PWL operational baselines.
Stage 3 requires stage2_baselines.csv and stage2_reference_design.csv.
If capacities change, rerun Stage 2. Do not compensate with tolerances.
