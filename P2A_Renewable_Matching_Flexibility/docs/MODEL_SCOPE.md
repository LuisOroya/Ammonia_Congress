# Model scope

This note prevents common overinterpretations of the outputs.

- The P2A chain includes PV, wind, grid exchange, PEM electrolyzer, BOP, H2 compressor/storage, ASU, N2 compressor, and Haber–Bosch electricity demand.
- The renewable-matching boundary is PEM stack + BOP (`MATCH_FULL_P2A = 0`). Other auxiliary loads may use grid electricity.
- The six-segment SB-PWL PEM model is hourly and steady-state. It does not model electrolyzer startup delays or degradation.
- Haber–Bosch production is constrained to 80–100% of rated production when operating in this formulation; no detailed thermal dynamics, startup, or minimum-up/down model is included.
- Stage-3 `DeltaP` is a guaranteed minimum sustained deviation of gross plant electrical demand during the activation window. The actual deviation can exceed `DeltaP` in individual hours.
- Stage 3 measures technical feasibility under the model; it does not impose an activation-price/profitability test or a net-grid reserve-delivery contract.
- Recovery can occur over the remaining representative month while maintaining the ammonia-production requirement and terminal H2 inventory.

## PEM preprocessing boundary

The nonlinear electrochemical PEM model is a preprocessing model used to construct the capacity-normalized production curve and PWL coefficients. The MILP optimization stages do not solve the nonlinear electrochemical equations. They use the exact segment-binary representation of the generated six-segment PWL curve. The six-segment count is a fixed study configuration; dynamic programming optimizes breakpoint locations conditional on that count.
