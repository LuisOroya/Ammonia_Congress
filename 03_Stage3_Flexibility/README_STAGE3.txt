STAGE 3 - PAIRED PHYS-vs-RM FLEXIBILITY
=======================================
Uses V5 compressed-history logic and exact renewable matching (no RM tolerance).

Before AMPL:
  python prepare_stage3_baselines.py
This reads ../02_Stage2_Baselines/stage2_baselines.csv, checks the reference
capacities, and writes flex_baselines_2025.dat.

Then:
  include main_flex_smoke.run;

If clean, proceed to main_flex_pilot_24h.run and later main_flex_dev_6h.run.
