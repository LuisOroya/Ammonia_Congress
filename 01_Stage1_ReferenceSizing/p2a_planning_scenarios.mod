# ============================================================
# p2a_planning_scenarios.mod
# Two-stage stochastic / multi-scenario RES portfolio planning
# for the fixed Power-to-Ammonia process.
#
# FIRST STAGE (scenario-independent):
#   P_PV_MAX, P_WD_MAX, H2_ST_MAX
#
# SECOND STAGE (scenario-dependent):
#   hourly P2A and grid operation for each monthly scenario.
#
# The conversion-process capacities remain FIXED.
# PV, wind, and H2 storage are co-designed under STRICT HOURLY MATCHING.
# ============================================================

# -------------------------
# Scenario structure
# -------------------------
set S ordered;
param TMAX integer > 0;
set T ordered := 1..TMAX;
set T0 ordered := 0..TMAX;

param NPER {S} integer > 0, <= TMAX;
param PROB {S} >= 0, <= 1;
check: abs(sum {s in S} PROB[s] - 1) <= 1e-8;

param dt > 0;
set N ordered;

# Hourly normalized renewable profiles [p.u.]
# Values for t > NPER[s] are ignored.
param zeta_PV {S,T} >= 0, <= 1 default 0;
param zeta_WD {S,T} >= 0, <= 1 default 0;

# -------------------------
# Planning economics
# -------------------------
# CAPEX: USD/MW
# FOM:   USD/(MW-year)
# CRF annualizes the investment term.
param CAPEX_PV >= 0;
param CAPEX_WD >= 0;
param FOM_PV >= 0;
param FOM_WD >= 0;

# H2 storage economics: CAPEX in USD/kgH2 and FOM in USD/(kgH2-year).
# A separate CRF is retained so the tank lifetime can later differ from PV/WD.
param CAPEX_H2_ST >= 0;
param FOM_H2_ST >= 0;
param CRF > 0;
param CRF_H2_ST > 0;

# Each representative scenario is one month. If PROB is the
# probability/frequency of a representative month, multiplying the
# expected monthly operating cost by 12 yields annual-equivalent OPEX.
param MONTHS_PER_YEAR > 0 default 12;

# Grid import price and a very small export penalty [USD/MWh].
# Export is permitted to dispose of renewable surplus, but is not
# treated as a revenue stream in this compact reference design.
param C_GRID >= 0;
param EPS_EXPORT >= 0;

# -------------------------
# Matching rule used for DESIGN
# -------------------------
param MATCH_FRACTION >= 0, <= 1 default 1;
param MATCH_FULL_P2A binary default 0;

# -------------------------
# Fixed PEM
# -------------------------
param P_EL_MAX > 0;
param H2_PROD_RATED > 0;
param L {N} >= 0, <= 1;
param U {N} >= 0, <= 1;
param A {N};
param B {N};
param SEC_BOP >= 0;

# -------------------------
# H2 subsystem
# -------------------------
param SEC_H2_COMP >= 0;
param H2_COMP_MAX > 0;
param H2_ST_MIN_FRAC >= 0, <= 1;
param H2_ST_MAX_FRAC >= 0, <= 1;
param H2_ST_INIT_FRAC >= 0, <= 1;

# -------------------------
# Fixed N2 / NH3 subsystem
# -------------------------
param LAMBDA_H2_NH3 > 0;
param LAMBDA_N2_NH3 > 0;
param N2_ASU_MAX > 0;
param N2_COMP_MAX > 0;
param SEC_ASU >= 0;
param SEC_N2_COMP >= 0;
param Q_NH3_MAX > 0;
param HB_MIN_LOAD >= 0, <= 1;
param SEC_HB >= 0;
param NH3_REQ_FRAC >= HB_MIN_LOAD, <= 1;

# ============================================================
# FIRST-STAGE VARIABLES: COMMON TO ALL SCENARIOS
# ============================================================
var P_PV_MAX >= 0;
var P_WD_MAX >= 0;
var H2_ST_MAX >= 0;   # [kgH2] installed H2 storage capacity

# ============================================================
# SECOND-STAGE VARIABLES: SCENARIO-DEPENDENT OPERATION
# Only indices satisfying t <= NPER[s] are used by constraints/objective.
# ============================================================
var p_pv      {S,T} >= 0;
var p_wd      {S,T} >= 0;
var p_pv_curt {S,T} >= 0;
var p_wd_curt {S,T} >= 0;

var p_grid_imp {S,T} >= 0;
var p_grid_exp {S,T} >= 0;

var p_el_stack {S,T} >= 0;
var p_el_seg {N,S,T} >= 0;
var y_seg {N,S,T} binary;
var h2_prod {S,T} >= 0;

var p_bop     {S,T} >= 0;
var p_h2_comp {S,T} >= 0;
var p_asu     {S,T} >= 0;
var p_n2_comp {S,T} >= 0;
var p_hb      {S,T} >= 0;

var h2_st {S,T0} >= 0;
var h2_hb {S,T} >= 0;
var n2_prod {S,T} >= 0;
var nh3_prod {S,T} >= 0;

var p_p2a {S,T} >= 0;
var p_match_load {S,T} >= 0;

# ============================================================
# OBJECTIVE
# Annualized first-stage investment + fixed O&M
# + annual-equivalent expected monthly grid operating cost.
# ============================================================
minimize AnnualizedExpectedCost:
      (CRF * CAPEX_PV + FOM_PV) * P_PV_MAX
    + (CRF * CAPEX_WD + FOM_WD) * P_WD_MAX
    + (CRF_H2_ST * CAPEX_H2_ST + FOM_H2_ST) * H2_ST_MAX
    + MONTHS_PER_YEAR
      * sum {s in S} PROB[s]
        * sum {t in T: t <= NPER[s]}
          (C_GRID * p_grid_imp[s,t]
          + EPS_EXPORT * p_grid_exp[s,t]) * dt;

# ============================================================
# RENEWABLE GENERATION AND GRID BALANCE
# ============================================================
subject to PV_Availability {s in S, t in T: t <= NPER[s]}:
    p_pv[s,t] + p_pv_curt[s,t]
    = P_PV_MAX * zeta_PV[s,t];

subject to WD_Availability {s in S, t in T: t <= NPER[s]}:
    p_wd[s,t] + p_wd_curt[s,t]
    = P_WD_MAX * zeta_WD[s,t];

subject to PowerBalance {s in S, t in T: t <= NPER[s]}:
    p_pv[s,t] + p_wd[s,t] + p_grid_imp[s,t]
    = p_p2a[s,t] + p_grid_exp[s,t];

# ============================================================
# PEM ELECTROLYZER
# ============================================================
subject to EL_Power_Decomposition {s in S, t in T: t <= NPER[s]}:
    p_el_stack[s,t] = sum {n in N} p_el_seg[n,s,t];

subject to EL_Segment_Lower {n in N, s in S, t in T: t <= NPER[s]}:
    p_el_seg[n,s,t] >= L[n] * P_EL_MAX * y_seg[n,s,t];

subject to EL_Segment_Upper {n in N, s in S, t in T: t <= NPER[s]}:
    p_el_seg[n,s,t] <= U[n] * P_EL_MAX * y_seg[n,s,t];

subject to EL_One_Segment {s in S, t in T: t <= NPER[s]}:
    sum {n in N} y_seg[n,s,t] <= 1;

subject to EL_Stack_Capacity {s in S, t in T: t <= NPER[s]}:
    p_el_stack[s,t] <= P_EL_MAX;

subject to H2_Production_PWL {s in S, t in T: t <= NPER[s]}:
    h2_prod[s,t]
    = sum {n in N}
        (A[n] * p_el_seg[n,s,t]
        + B[n] * P_EL_MAX * y_seg[n,s,t]);

subject to BOP_Power {s in S, t in T: t <= NPER[s]}:
    p_bop[s,t] = SEC_BOP * h2_prod[s,t];

subject to H2_Compressor_Power {s in S, t in T: t <= NPER[s]}:
    p_h2_comp[s,t] = SEC_H2_COMP * h2_prod[s,t];

subject to H2_Compressor_Capacity {s in S, t in T: t <= NPER[s]}:
    h2_prod[s,t] <= H2_COMP_MAX;

# ============================================================
# H2 STORAGE
# H2_ST_MAX is a scenario-independent first-stage sizing variable.
# Each monthly scenario starts and ends at the same prescribed inventory
# fraction of the installed tank capacity.
# ============================================================
subject to H2_Storage_Balance {s in S, t in T: t <= NPER[s]}:
    h2_st[s,t]
    = h2_st[s,t-1] + dt * (h2_prod[s,t] - h2_hb[s,t]);

subject to H2_Storage_Lower {s in S, t in T0: t <= NPER[s]}:
    h2_st[s,t] >= H2_ST_MIN_FRAC * H2_ST_MAX;

subject to H2_Storage_Upper {s in S, t in T0: t <= NPER[s]}:
    h2_st[s,t] <= H2_ST_MAX_FRAC * H2_ST_MAX;

subject to H2_Storage_Initial {s in S}:
    h2_st[s,0] = H2_ST_INIT_FRAC * H2_ST_MAX;

subject to H2_Storage_Terminal {s in S}:
    h2_st[s,NPER[s]] = H2_ST_INIT_FRAC * H2_ST_MAX;

# ============================================================
# N2 / NH3 PROCESS
# ============================================================
subject to H2_to_HB {s in S, t in T: t <= NPER[s]}:
    h2_hb[s,t] = LAMBDA_H2_NH3 * nh3_prod[s,t];

subject to N2_to_HB {s in S, t in T: t <= NPER[s]}:
    n2_prod[s,t] = LAMBDA_N2_NH3 * nh3_prod[s,t];

subject to ASU_Capacity {s in S, t in T: t <= NPER[s]}:
    n2_prod[s,t] <= N2_ASU_MAX;

subject to N2_Compressor_Capacity {s in S, t in T: t <= NPER[s]}:
    n2_prod[s,t] <= N2_COMP_MAX;

subject to ASU_Power {s in S, t in T: t <= NPER[s]}:
    p_asu[s,t] = SEC_ASU * n2_prod[s,t];

subject to N2_Compressor_Power {s in S, t in T: t <= NPER[s]}:
    p_n2_comp[s,t] = SEC_N2_COMP * n2_prod[s,t];

subject to HB_Minimum_Load {s in S, t in T: t <= NPER[s]}:
    nh3_prod[s,t] >= HB_MIN_LOAD * Q_NH3_MAX;

subject to HB_Maximum_Load {s in S, t in T: t <= NPER[s]}:
    nh3_prod[s,t] <= Q_NH3_MAX;

subject to HB_Power {s in S, t in T: t <= NPER[s]}:
    p_hb[s,t] = SEC_HB * nh3_prod[s,t];

subject to Monthly_NH3_Requirement {s in S}:
    sum {t in T: t <= NPER[s]} nh3_prod[s,t] * dt
    = NH3_REQ_FRAC * Q_NH3_MAX * NPER[s] * dt;

subject to Total_P2A_Power {s in S, t in T: t <= NPER[s]}:
    p_p2a[s,t]
    = p_el_stack[s,t]
    + p_bop[s,t]
    + p_h2_comp[s,t]
    + p_asu[s,t]
    + p_n2_comp[s,t]
    + p_hb[s,t];

# ============================================================
# STRICT HOURLY RENEWABLE MATCHING USED IN PLANNING
# Current boundary: PEM stack + PEM BOP when MATCH_FULL_P2A = 0.
# ============================================================
subject to Matching_Load_Definition {s in S, t in T: t <= NPER[s]}:
    p_match_load[s,t]
    = (1 - MATCH_FULL_P2A) * (p_el_stack[s,t] + p_bop[s,t])
    + MATCH_FULL_P2A * p_p2a[s,t];

subject to Hourly_Renewable_Matching {s in S, t in T: t <= NPER[s]}:
    p_pv[s,t] + p_wd[s,t]
    >= MATCH_FRACTION * p_match_load[s,t];
