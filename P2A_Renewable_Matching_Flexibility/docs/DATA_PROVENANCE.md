# Data provenance and scenario inputs

## PEM conversion curve

The nonlinear PEM implementation and dynamic-programming PWL procedure are preserved under `00_pem_curve/`. The script version is authoritative for reproducibility; the notebook is retained for transparency and plots. The final optimization uses six segments generated from 1,000 candidate normalized-power points over `[0.15,1.00]`.

The supplied project contains precomputed representative monthly scenario sets for K=5,...,15. These files are preserved under `01_stage1_reference_sizing/scenario_sets/` and are treated as immutable inputs to the reproducibility workflow.

The selected set for downstream analysis is **K=9**, containing representative months:

- S1: 2017-05
- S2: 2019-07
- S3: 2020-02
- S4: 2020-04
- S5: 2021-12
- S6: 2023-05
- S7: 2024-08
- S8: 2024-11
- S9: 2025-09

The probabilities and month lengths are stored in `scenario_sets/K09/planning_scenarios.dat`.

## Current reproducibility boundary

The original raw renewable archive, feature-scaling code, K-medoids implementation, and fidelity metrics used to select K=9 were not present in the supplied ZIP used for this cleanup. Therefore the repository can verify and reproduce the optimization **conditional on the supplied scenario sets**, but cannot recreate the scenario-reduction step from raw data.

Before public release, add the raw-data source/license, location or spatial aggregation, timezone/timestamp convention, preprocessing, clustering features/scaling, distance metric, medoid-selection procedure, and the fidelity criterion used to select K=9. If raw data cannot be redistributed, provide a download script or exact public source and checksums where licensing permits.
