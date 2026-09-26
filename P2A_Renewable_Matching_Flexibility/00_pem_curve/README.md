# Stage 0 — PEM curve and dynamic-programming PWL approximation

This directory makes the electrolyzer conversion curve used by Stages 1–3 reproducible rather than treating the PWL coefficients as unexplained constants.

## Nonlinear PEM curve

`generate_pem_pwl.py` is a script version of the supplied research notebook. The reference operating point is a 94.7 MW PEM stack at 60 °C and 30 bar on both electrodes, with a maximum current density of 2 A/cm². The electrochemical implementation includes reversible, activation, ohmic, and diffusion voltage terms and the adopted Faradaic-efficiency correlation.

The optimization model does **not** use this nonlinear electrochemical model directly. It uses a capacity-normalized hydrogen-production function

`h(x) = m_H2(x) / P_EL,max`, with `x = P_EL / P_EL,max`,

over the productive interval `x ∈ [0.15, 1.00]`.

## Breakpoint selection

The PWL breakpoints are not equally spaced. The preprocessing procedure is:

1. Invert the monotone current-density/power relation on a dense 50,000-point grid.
2. Evaluate the nonlinear PEM production function at exactly 1,000 uniformly spaced candidate normalized-power points on `[0.15, 1.00]`.
3. For every candidate endpoint pair `(i,j)`, construct the chord through the nonlinear curve at those endpoints.
4. Compute its sum of squared errors over the enclosed candidate points,
   `E_ij = Σ_k [h_k - h_hat_ij(x_k)]²`.
5. Use dynamic programming to select the breakpoint subset minimizing total SSE for a fixed number of segments. The solution is globally optimal **within the 1,000-point candidate partition**.
6. Recover each segment as `h(x)=A_n x+B_n`, which yields the MILP-ready relation
   `m_H2 = A_n P_EL + B_n P_EL,max`.

The script compares 3, 5, 6, 9, 12, and 15 segments. The conference study adopts **six segments** as its fixed fidelity/complexity configuration. This is a modeling choice, not an automatically selected number of segments; no formal elbow or threshold-selection rule is encoded.

For six segments, the breakpoints are approximately

`[0.15000, 0.26401, 0.38909, 0.52523, 0.67242, 0.83068, 1.00000]`.

On the 1,000-point master curve, the six-segment model has RMSE ≈ `0.01169755 kg/MWh` (`0.063452%` of rated normalized production) and maximum absolute error ≈ `0.01783739 kg/MWh` (`0.096756%`). The generated chord approximation does not overestimate the nonlinear curve at the master points.

## Reproduce

From the repository root:

```powershell
py 00_pem_curve/generate_pem_pwl.py
```

The optimization-ready file is

`00_pem_curve/generated/pem_pwl_6segments.dat`.

Stages 1–3 load this single generated file; the coefficients are no longer duplicated across three `.dat` files.

The cleaned notebook is retained in `00_pem_curve/notebooks/` for transparency and plots. The script is the authoritative reproducible implementation used by the pipeline.
