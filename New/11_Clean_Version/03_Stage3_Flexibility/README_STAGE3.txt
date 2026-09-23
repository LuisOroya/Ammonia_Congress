STAGE 3 - FINAL K=9 PAIRED PHYS/RM FLEXIBILITY
===============================================

PURPOSE
-------
Quantify how much of the physically feasible P2A load flexibility remains
available when temporal renewable matching must continue to be satisfied.

For each Stage-2 baseline case:
  c=1 MONTHLY matching
  c=2 HOURLY matching

and each selected (scenario, activation start, duration, direction), solve:
  PHYS : matching relaxed from the activation instant onward
  RM   : baseline matching rule retained

Both branches use the SAME Stage-2 state and realized accounting history.
The no-matching Stage-2 baseline is not paired because RM and PHYS would be
identical by definition.

PHYSICAL REQUIREMENTS RETAINED IN BOTH BRANCHES
-----------------------------------------------
- exact SB-PWL PEM conversion model
- same H2 inventory immediately before activation
- same cumulative NH3 production before activation
- same total monthly NH3 delivery as the Stage-2 baseline
- same terminal H2 inventory as the Stage-2 baseline
- fixed Stage-1 PV, wind, and H2-storage capacities
- no simultaneous grid import/export in Stage 3

Only t >= tau is reoptimized. The already-realized prefix is represented by
Stage-2 H2 state and cumulative NH3 / renewable-matching accounting histories.

ACTIVATION
----------
Durations: 1, 4, 12, 24 h.
INC: p_P2A(t) >= p_P2A^0(t) + DeltaP during activation.
DEC: p_P2A(t) <= p_P2A^0(t) - DeltaP during activation.
Objective: maximize the guaranteed sustained DeltaP.
Overshoot is allowed.

RETAINED FLEXIBILITY
--------------------
For F_PHYS > numerical tolerance:
  R = F_RM / F_PHYS
and absolute loss:
  DeltaF = F_PHYS - F_RM.

SOLVER
------
AMPL + Gurobi 13.0.3.
The run files use mipgap=0, mipfocus=2, presolve=2, threads=16.

HOW TO RUN
----------
1) Stage 2 must already have produced the final independent-scenario file:
     ../02_Stage2_Baselines/stage2_baselines.csv

2) Prepare the Stage-3 baseline .dat file once:
     py prepare_stage3_inputs.py

   A prepared stage3_baselines_k09.dat is already included in this package,
   generated from the final Stage-2 results supplied on 2026-09-21. Re-run the
   Python script only if Stage 2 is changed.

3) VALIDATE FIRST:
     include main_stage3_pilot.run;

   Pilot = stress scenario s=4 (April 2020), monthly/hourly baselines,
   4 durations, and 4 distributed activation starts.
   Check that no material RM > PHYS warning appears.

4) Analyze pilot:
     py analyze_stage3_results.py stage3_pilot_results.csv

5) Then run the final K=9 sweep:
     include main_stage3_k09.run;

   Structured activation sampling uses 00/06/12/18 h every 7 days.
   This can be changed with DAY_STEP and START_CLOCK in the run file.

6) Analyze final output:
     py analyze_stage3_results.py stage3_flexibility_results.csv

FINAL OUTPUTS
-------------
stage3_flexibility_results.csv   paired event-level PHYS/RM results
stage3_scenario_summary.csv      event statistics within each representative month
stage3_retention_summary.csv     probability-weighted K=9 results

IMPORTANT CHECK
---------------
RM is an additional constraint relative to PHYS for the same baseline event,
therefore F_RM should not materially exceed F_PHYS. The run and analysis
scripts explicitly flag violations larger than 1e-3 MW.

Numerical replay note (v6): BASE_REPLAY_TOL is used only to avoid infeasibility from CSV/model replay precision. Reported flexibility subtracts this tolerance, so a raw DeltaP equal to BASE_REPLAY_TOL is reported as 0 MW.

V7 reporting note:
- FLEX_ZERO_TOL = 1e-3 MW (1 kW); this is a reporting threshold only.
- The analyzer normalizes probabilities when the input contains only a subset
  of K=9 scenarios (e.g., the pilot), and reports probability_coverage.
