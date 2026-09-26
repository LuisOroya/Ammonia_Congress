# ============================================================
# p2a_stage2_fixed_baselines_sbpwl.mod
# Stage 2A - EXACT SB-PWL fixed-installation operational baselines
#
# IMPORTANT COMPUTATIONAL STRUCTURE
# ---------------------------------
# A single representative scenario is active in each optimization.
# The run file loops over all (scenario, matching-case) pairs.
# This preserves the mathematical Stage-2 definition while avoiding
# one large monolithic MILP containing all representative months.
#
# Cases selected by the run file:
#   C0 = no renewable matching
#   C1 = monthly matching
#   C2 = hourly matching
#
# Baseline selection for EACH (s,c):
#   Stage A: minimize grid-related operating cost
#   Stage B: retain Stage-A cost and minimize normalized process variability
#            (electrolyzer-load and ammonia-production total variation)
# ============================================================

set S ordered;
param TMAX integer > 0;
set T ordered := 1..TMAX;
set T0 ordered := 0..TMAX;

param NPER {S} integer > 0, <= TMAX;
param PROB {S} >= 0, <= 1;
check: abs(sum {s in S} PROB[s] - 1) <= 1e-8;

param dt > 0;
set N ordered;

param zeta_PV {S,T} >= 0, <= 1 default 0;
param zeta_WD {S,T} >= 0, <= 1 default 0;

# Scenario solved in the current MILP. The .run file changes this value.
param ACTIVE_SCEN integer default 1;
check: ACTIVE_SCEN in S;

# ------------------------------------------------------------
# Fixed installation
# ------------------------------------------------------------
param P_PV_MAX > 0;
param P_WD_MAX > 0;
param H2_ST_MAX > 0;

# ------------------------------------------------------------
# Matching switches
# ------------------------------------------------------------
param MATCH_MONTHLY binary default 0;
param MATCH_HOURLY  binary default 0;
check: MATCH_MONTHLY + MATCH_HOURLY <= 1;

param MATCH_FRACTION >= 0, <= 1 default 1;
param MATCH_FULL_P2A binary default 0;

# ------------------------------------------------------------
# Exact SB-PWL PEM
# ------------------------------------------------------------
param P_EL_MAX > 0;
param H2_PROD_RATED > 0;
param L {N} >= 0, <= 1;
param U {N} >= 0, <= 1;
param A {N};
param B {N};
param SEC_BOP >= 0;

# H2 subsystem
param SEC_H2_COMP >= 0;
param H2_COMP_MAX > 0;
param H2_ST_MIN_FRAC >= 0, <= 1;
param H2_ST_MAX_FRAC >= 0, <= 1;
param H2_ST_INIT_FRAC >= 0, <= 1;

# N2 / NH3 subsystem
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

# Grid objective
param C_GRID >= 0;
param EPS_EXPORT >= 0;

# Per-scenario lexicographic cost lock; set by the .run file after Stage A.
param COST_LOCK >= 0 default 0;
param COST_LOCK_EPS >= 0 default 0.001;

# ============================================================
# Variables - only the active scenario is instantiated
# ============================================================
var p_pv      {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_wd      {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_pv_curt {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_wd_curt {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;

var p_grid_imp {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_grid_exp {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;

# Exact segment-binary PEM representation
var p_el_stack {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_el_seg   {n in N, t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var y_seg      {n in N, t in T: t <= NPER[ACTIVE_SCEN]} binary;
var h2_prod    {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;

var p_bop      {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_h2_comp  {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_asu      {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_n2_comp  {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_hb       {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;

var h2_st    {t in T0: t <= NPER[ACTIVE_SCEN]} >= 0;
var h2_hb    {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var n2_prod  {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var nh3_prod {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;

var p_p2a        {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;
var p_match_load {t in T: t <= NPER[ACTIVE_SCEN]} >= 0;

# Absolute-ramp variables for the Stage-B tie-breaker.
var ramp_el_abs  {t in T: 2 <= t and t <= NPER[ACTIVE_SCEN]} >= 0;
var ramp_nh3_abs {t in T: 2 <= t and t <= NPER[ACTIVE_SCEN]} >= 0;

# ============================================================
# Objectives
# ============================================================

# Primary economic baseline for the active scenario.
minimize ScenarioOperatingCost:
    sum {t in T: t <= NPER[ACTIVE_SCEN]}
      (C_GRID * p_grid_imp[t]
       + EPS_EXPORT * p_grid_exp[t]) * dt;

# Secondary tie-breaker for the active scenario.
minimize ScenarioNormalizedVariability:
    sum {t in T: 2 <= t and t <= NPER[ACTIVE_SCEN]}
      (ramp_el_abs[t] / P_EL_MAX
       + ramp_nh3_abs[t] / Q_NH3_MAX);

# This constraint is DROPPED for Stage A and RESTORED for Stage B.
subject to PrimaryCostLock:
    sum {t in T: t <= NPER[ACTIVE_SCEN]}
      (C_GRID * p_grid_imp[t]
       + EPS_EXPORT * p_grid_exp[t]) * dt
    <= COST_LOCK;

# Absolute-ramp linearization used by Stage B.
subject to EL_Ramp_Abs_Pos {t in T: 2 <= t and t <= NPER[ACTIVE_SCEN]}:
    ramp_el_abs[t] >= p_el_stack[t] - p_el_stack[t-1];

subject to EL_Ramp_Abs_Neg {t in T: 2 <= t and t <= NPER[ACTIVE_SCEN]}:
    ramp_el_abs[t] >= p_el_stack[t-1] - p_el_stack[t];

subject to NH3_Ramp_Abs_Pos {t in T: 2 <= t and t <= NPER[ACTIVE_SCEN]}:
    ramp_nh3_abs[t] >= nh3_prod[t] - nh3_prod[t-1];

subject to NH3_Ramp_Abs_Neg {t in T: 2 <= t and t <= NPER[ACTIVE_SCEN]}:
    ramp_nh3_abs[t] >= nh3_prod[t-1] - nh3_prod[t];

# ============================================================
# Renewable availability and electrical balance
# ============================================================
subject to PV_Availability {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_pv[t] + p_pv_curt[t]
    = P_PV_MAX * zeta_PV[ACTIVE_SCEN,t];

subject to WD_Availability {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_wd[t] + p_wd_curt[t]
    = P_WD_MAX * zeta_WD[ACTIVE_SCEN,t];

subject to PowerBalance {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_pv[t] + p_wd[t] + p_grid_imp[t]
    = p_p2a[t] + p_grid_exp[t];

# ============================================================
# PEM electrolyzer - EXACT segment-binary PWL
# ============================================================
subject to EL_Power_Decomposition {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_el_stack[t] = sum {n in N} p_el_seg[n,t];

subject to EL_Segment_Lower
    {n in N, t in T: t <= NPER[ACTIVE_SCEN]}:
    p_el_seg[n,t] >= L[n] * P_EL_MAX * y_seg[n,t];

subject to EL_Segment_Upper
    {n in N, t in T: t <= NPER[ACTIVE_SCEN]}:
    p_el_seg[n,t] <= U[n] * P_EL_MAX * y_seg[n,t];

subject to EL_One_Segment {t in T: t <= NPER[ACTIVE_SCEN]}:
    sum {n in N} y_seg[n,t] <= 1;

subject to EL_Stack_Capacity {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_el_stack[t] <= P_EL_MAX;

subject to H2_Production_PWL {t in T: t <= NPER[ACTIVE_SCEN]}:
    h2_prod[t]
    = sum {n in N}
        (A[n] * p_el_seg[n,t]
         + B[n] * P_EL_MAX * y_seg[n,t]);

subject to BOP_Power {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_bop[t] = SEC_BOP * h2_prod[t];

# ============================================================
# H2 compression and storage
# ============================================================
subject to H2_Compressor_Power {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_h2_comp[t] = SEC_H2_COMP * h2_prod[t];

subject to H2_Compressor_Capacity {t in T: t <= NPER[ACTIVE_SCEN]}:
    h2_prod[t] <= H2_COMP_MAX;

subject to H2_Storage_Balance {t in T: t <= NPER[ACTIVE_SCEN]}:
    h2_st[t] = h2_st[t-1] + dt * (h2_prod[t] - h2_hb[t]);

subject to H2_Storage_Lower {t in T0: t <= NPER[ACTIVE_SCEN]}:
    h2_st[t] >= H2_ST_MIN_FRAC * H2_ST_MAX;

subject to H2_Storage_Upper {t in T0: t <= NPER[ACTIVE_SCEN]}:
    h2_st[t] <= H2_ST_MAX_FRAC * H2_ST_MAX;

subject to H2_Storage_Initial:
    h2_st[0] = H2_ST_INIT_FRAC * H2_ST_MAX;

subject to H2_Storage_Terminal:
    h2_st[NPER[ACTIVE_SCEN]] = H2_ST_INIT_FRAC * H2_ST_MAX;

# ============================================================
# N2 / NH3 process
# ============================================================
subject to H2_to_HB {t in T: t <= NPER[ACTIVE_SCEN]}:
    h2_hb[t] = LAMBDA_H2_NH3 * nh3_prod[t];

subject to N2_to_HB {t in T: t <= NPER[ACTIVE_SCEN]}:
    n2_prod[t] = LAMBDA_N2_NH3 * nh3_prod[t];

subject to ASU_Capacity {t in T: t <= NPER[ACTIVE_SCEN]}:
    n2_prod[t] <= N2_ASU_MAX;

subject to N2_Compressor_Capacity {t in T: t <= NPER[ACTIVE_SCEN]}:
    n2_prod[t] <= N2_COMP_MAX;

subject to ASU_Power {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_asu[t] = SEC_ASU * n2_prod[t];

subject to N2_Compressor_Power {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_n2_comp[t] = SEC_N2_COMP * n2_prod[t];

subject to HB_Minimum_Load {t in T: t <= NPER[ACTIVE_SCEN]}:
    nh3_prod[t] >= HB_MIN_LOAD * Q_NH3_MAX;

subject to HB_Maximum_Load {t in T: t <= NPER[ACTIVE_SCEN]}:
    nh3_prod[t] <= Q_NH3_MAX;

subject to HB_Power {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_hb[t] = SEC_HB * nh3_prod[t];

subject to Monthly_NH3_Requirement:
    sum {t in T: t <= NPER[ACTIVE_SCEN]} nh3_prod[t] * dt
    = NH3_REQ_FRAC * Q_NH3_MAX * NPER[ACTIVE_SCEN] * dt;

subject to Total_P2A_Power {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_p2a[t]
    = p_el_stack[t]
      + p_bop[t]
      + p_h2_comp[t]
      + p_asu[t]
      + p_n2_comp[t]
      + p_hb[t];

# ============================================================
# Matching load and temporal matching cases
# ============================================================
subject to Matching_Load_Definition {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_match_load[t]
    = (1 - MATCH_FULL_P2A) * (p_el_stack[t] + p_bop[t])
      + MATCH_FULL_P2A * p_p2a[t];

# Monthly balance over the actual length of the active scenario.
subject to Monthly_Renewable_Matching:
    sum {t in T: t <= NPER[ACTIVE_SCEN]} (p_pv[t] + p_wd[t]) * dt
    >= MATCH_MONTHLY * MATCH_FRACTION
       * sum {t in T: t <= NPER[ACTIVE_SCEN]} p_match_load[t] * dt;

subject to Hourly_Renewable_Matching {t in T: t <= NPER[ACTIVE_SCEN]}:
    p_pv[t] + p_wd[t]
    >= MATCH_HOURLY * MATCH_FRACTION * p_match_load[t];
