STAGE 1 - REFERENCE SIZING
==========================
Exact SB-PWL multi-scenario sizing of PV, wind and H2 storage around the fixed
P2A conversion plant. Current 2025 months are provisional scenarios.

Run: include main_planning_2025.run;

Outputs include the numerical optimum and an upward-rounded reference design.
The rounded design is what must be used consistently by Stages 2 and 3.
After rerunning Stage 1, run ../sync_reference_design.py from the ZIP root.
