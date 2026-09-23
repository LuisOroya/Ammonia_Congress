P2A CONGRESS WORKFLOW — K=9 SELECTED FRAMEWORK
=============================================

Scenario selection
------------------
K=9 is the selected representative monthly scenario set according to the
scenario-selection metrics. Planning runs for K=8--13 provide a supporting
consistency check but do not define K.

Stage 1 - Reference design
--------------------------
Use the stored K09 planning result. Conservative upward-rounded design used
for downstream operation:
  PV = 159.96 MW
  Wind = 499.30 MW
  H2 storage = 27920 kg

Stage 2 - Baseline operation
----------------------------
Three cases only:
  C0 no matching
  C1 monthly matching
  C2 hourly matching

Every (scenario, matching-case) pair is solved independently.
For EACH pair, baseline selection uses two lexicographic levels:
  A) minimize grid-related operating cost;
  B) with that scenario's Stage-A cost locked within 0.001 USD, minimize
     normalized total variation of electrolyzer load and ammonia production.

With K=9, Stage 2 therefore runs 9 x 3 x 2 = 54 smaller solves instead of six
large multi-scenario solves. Scenario probabilities are used only to aggregate
final case-level reporting and do not affect the individual baseline schedule.

Run from 02_Stage2_Baselines:
  include main_stage2_2025_baselines_sbpwl.run;

Use Gurobi 13.0.3 for the final Stage-2/Stage-3 paper results.

Stage 3 - Paired flexibility
----------------------------
Stage 3 will use the saved Stage-2 baselines and the same K=9 scenarios.
PHYS relaxes matching after activation; RM retains the baseline case's
matching requirement from the identical baseline state/history.

Synchronization
---------------
Run `py sync_reference_design.py` from 11_Clean_Version whenever the selected
K=9 design/scenario files need to be restored into downstream stages.

FINAL STAGE-3 UPDATE (2026-09-21)
--------------------------------
Stage 3 is now implemented in 03_Stage3_Flexibility using the final K=9
independent-scenario Stage-2 baselines. Run prepare_stage3_inputs.py, then
main_stage3_pilot.run, then main_stage3_k09.run after validation.
