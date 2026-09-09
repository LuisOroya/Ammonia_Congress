# ============================================================
# p2a_paired_flex_exact_sbpwl.mod
# Exact SB-PWL paired PHYS-vs-RM flexibility evaluation.
#
# Baseline cases:
#   1 = monthly matching
#   2 = weekly matching (168-h non-overlapping blocks)
#   3 = hourly matching
#
# For each (scenario, case, tau, duration, direction):
#   PHYS: renewable matching removed
#   RM:   the baseline case's matching rule retained
#
# Both envelopes use the SAME baseline and exact same pre-activation state.
# ============================================================

set SCENS ordered;
set CASES ordered;
set DURS ordered;
param TMAX integer > 0;
set T ordered := 1..TMAX;
set T0 ordered := 0..TMAX;
set N ordered;

param NPER {SCENS} integer > 0, <= TMAX;
param dt > 0;

param zeta_PV {SCENS,T} >= 0, <= 1 default 0;
param zeta_WD {SCENS,T} >= 0, <= 1 default 0;

# Fixed installation
param P_PV_MAX > 0;
param P_WD_MAX > 0;
param H2_ST_MAX > 0;

# Matching
param MATCH_MONTHLY binary default 0;
param MATCH_WEEKLY  binary default 0;
param MATCH_HOURLY  binary default 0;
check: MATCH_MONTHLY + MATCH_WEEKLY + MATCH_HOURLY <= 1;
param MATCH_FRACTION >= 0, <= 1;
param MATCH_FULL_P2A binary;
param WEEK_HOURS integer > 0;
param NWEEK integer > 0 := ceil(TMAX/WEEK_HOURS);
set W ordered := 1..NWEEK;

# Exact SB-PWL PEM
param P_EL_MAX > 0;
param H2_PROD_RATED > 0;
param L {N} >= 0, <= 1;
param U {N} >= 0, <= 1;
param A {N};
param B {N};
param SEC_BOP >= 0;

# H2
param SEC_H2_COMP >= 0;
param H2_COMP_MAX > 0;
param H2_ST_MIN_FRAC >= 0, <= 1;
param H2_ST_MAX_FRAC >= 0, <= 1;
param H2_ST_INIT_FRAC >= 0, <= 1;

# N2/NH3
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

param C_GRID >= 0;
param EPS_EXPORT >= 0;

# Saved exact Stage-2 baselines
param BASE_P2A      {SCENS,CASES,T} >= 0 default 0;
param BASE_PEL      {SCENS,CASES,T} >= 0 default 0;
param BASE_H2PROD   {SCENS,CASES,T} >= 0 default 0;
param BASE_NH3      {SCENS,CASES,T} >= 0 default 0;
param BASE_PV       {SCENS,CASES,T} >= 0 default 0;
param BASE_WD       {SCENS,CASES,T} >= 0 default 0;
param BASE_H2ST     {SCENS,CASES,T0} >= 0 default 0;
param BASE_MATCH_LOAD {s in SCENS, c in CASES, t in T} :=
    (1-MATCH_FULL_P2A)*(BASE_PEL[s,c,t] + SEC_BOP*BASE_H2PROD[s,c,t])
    + MATCH_FULL_P2A*BASE_P2A[s,c,t];

# Current test selected by run file
param SCEN_ACTIVE in SCENS;
param BASE_CASE in CASES;
param TAU_ACTIVE integer >= 1, <= TMAX;
param FLEX_INC binary default 0;
param FLEX_DEC binary default 0;
param ACTIVE {T} binary default 0;

# Optional lexicographic secondary solve
param LOCK_DELTA binary default 0;
param DELTA_TARGET >= 0 default 0;
param EPS_DELTA >= 0;

# Numerical controls
param FLEX_DELTA_MAX > 0;
param M_POWER > 0;
param M_GRID > 0;
param FLEX_ZERO_TOL >= 0;

# Results stored by the run file
param F_PHYS_INC {SCENS,CASES,DURS,T} >= 0 default 0;
param F_RM_INC   {SCENS,CASES,DURS,T} >= 0 default 0;
param F_PHYS_DEC {SCENS,CASES,DURS,T} >= 0 default 0;
param F_RM_DEC   {SCENS,CASES,DURS,T} >= 0 default 0;
param TESTED     {SCENS,CASES,DURS,T} binary default 0;

# ============================================================
# Variables
# ============================================================
var p_pv {T} >= 0;
var p_wd {T} >= 0;
var p_pv_curt {T} >= 0;
var p_wd_curt {T} >= 0;
var p_grid_imp {T} >= 0;
var p_grid_exp {T} >= 0;
# Explicit grid direction prevents simultaneous import/export from
# artificially satisfying renewable matching during a max-DeltaP solve.
var y_grid_import {T} binary;

var p_el_stack {T} >= 0;
var p_el_seg {N,T} >= 0;
var y_seg {N,T} binary;
var h2_prod {T} >= 0;

var p_bop {T} >= 0;
var p_h2_comp {T} >= 0;
var p_asu {T} >= 0;
var p_n2_comp {T} >= 0;
var p_hb {T} >= 0;

var h2_st {T0} >= 0;
var h2_hb {T} >= 0;
var n2_prod {T} >= 0;
var nh3_prod {T} >= 0;

var p_p2a {T} >= 0;
var p_match_load {T} >= 0;
var DeltaP >= 0, <= FLEX_DELTA_MAX;

# ============================================================
# Objectives
# ============================================================
maximize FlexibilityAmplitude: DeltaP;

minimize SecondaryOperatingCost:
    sum {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}
      (C_GRID*p_grid_imp[t] + EPS_EXPORT*p_grid_exp[t])*dt;

# ============================================================
# Plant model
# ============================================================
subject to PV_Availability {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_pv[t] + p_pv_curt[t] = P_PV_MAX*zeta_PV[SCEN_ACTIVE,t];

subject to WD_Availability {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_wd[t] + p_wd_curt[t] = P_WD_MAX*zeta_WD[SCEN_ACTIVE,t];

subject to PowerBalance {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_pv[t] + p_wd[t] + p_grid_imp[t] = p_p2a[t] + p_grid_exp[t];

subject to Grid_Import_Mode {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_grid_imp[t] <= M_GRID*y_grid_import[t];

subject to Grid_Export_Mode {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_grid_exp[t] <= M_GRID*(1-y_grid_import[t]);

subject to EL_Power_Decomposition {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_el_stack[t] = sum {n in N} p_el_seg[n,t];

subject to EL_Segment_Lower {n in N,t in T: t <= NPER[SCEN_ACTIVE]}:
    p_el_seg[n,t] >= L[n]*P_EL_MAX*y_seg[n,t];

subject to EL_Segment_Upper {n in N,t in T: t <= NPER[SCEN_ACTIVE]}:
    p_el_seg[n,t] <= U[n]*P_EL_MAX*y_seg[n,t];

subject to EL_One_Segment {t in T: t <= NPER[SCEN_ACTIVE]}:
    sum {n in N} y_seg[n,t] <= 1;

subject to EL_Stack_Capacity {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_el_stack[t] <= P_EL_MAX;

subject to H2_Production_PWL {t in T: t <= NPER[SCEN_ACTIVE]}:
    h2_prod[t] = sum {n in N}
      (A[n]*p_el_seg[n,t] + B[n]*P_EL_MAX*y_seg[n,t]);

subject to BOP_Power {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_bop[t] = SEC_BOP*h2_prod[t];

subject to H2_Compressor_Power {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_h2_comp[t] = SEC_H2_COMP*h2_prod[t];

subject to H2_Compressor_Capacity {t in T: t <= NPER[SCEN_ACTIVE]}:
    h2_prod[t] <= H2_COMP_MAX;

subject to H2_Storage_Balance {t in T: t <= NPER[SCEN_ACTIVE]}:
    h2_st[t] = h2_st[t-1] + dt*(h2_prod[t]-h2_hb[t]);

subject to H2_Storage_Lower {t in T0: t <= NPER[SCEN_ACTIVE]}:
    h2_st[t] >= H2_ST_MIN_FRAC*H2_ST_MAX;

subject to H2_Storage_Upper {t in T0: t <= NPER[SCEN_ACTIVE]}:
    h2_st[t] <= H2_ST_MAX_FRAC*H2_ST_MAX;

subject to H2_Storage_Initial:
    h2_st[0] = H2_ST_INIT_FRAC*H2_ST_MAX;

subject to H2_Storage_Terminal:
    h2_st[NPER[SCEN_ACTIVE]] = H2_ST_INIT_FRAC*H2_ST_MAX;

subject to H2_to_HB {t in T: t <= NPER[SCEN_ACTIVE]}:
    h2_hb[t] = LAMBDA_H2_NH3*nh3_prod[t];

subject to N2_to_HB {t in T: t <= NPER[SCEN_ACTIVE]}:
    n2_prod[t] = LAMBDA_N2_NH3*nh3_prod[t];

subject to ASU_Capacity {t in T: t <= NPER[SCEN_ACTIVE]}:
    n2_prod[t] <= N2_ASU_MAX;

subject to N2_Compressor_Capacity {t in T: t <= NPER[SCEN_ACTIVE]}:
    n2_prod[t] <= N2_COMP_MAX;

subject to ASU_Power {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_asu[t] = SEC_ASU*n2_prod[t];

subject to N2_Compressor_Power {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_n2_comp[t] = SEC_N2_COMP*n2_prod[t];

subject to HB_Minimum_Load {t in T: t <= NPER[SCEN_ACTIVE]}:
    nh3_prod[t] >= HB_MIN_LOAD*Q_NH3_MAX;

subject to HB_Maximum_Load {t in T: t <= NPER[SCEN_ACTIVE]}:
    nh3_prod[t] <= Q_NH3_MAX;

subject to HB_Power {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_hb[t] = SEC_HB*nh3_prod[t];

subject to Monthly_NH3_Requirement:
    sum {t in T: t <= NPER[SCEN_ACTIVE]} nh3_prod[t]*dt
    = NH3_REQ_FRAC*Q_NH3_MAX*NPER[SCEN_ACTIVE]*dt;

subject to Total_P2A_Power {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_p2a[t] = p_el_stack[t] + p_bop[t] + p_h2_comp[t]
              + p_asu[t] + p_n2_comp[t] + p_hb[t];

# ============================================================
# Renewable temporal matching with compressed pre-activation history
# ============================================================
subject to Matching_Load_Definition {t in T: t <= NPER[SCEN_ACTIVE]}:
    p_match_load[t]
    = (1-MATCH_FULL_P2A)*(p_el_stack[t]+p_bop[t])
      + MATCH_FULL_P2A*p_p2a[t];

# The realized prefix t < TAU_ACTIVE is taken from the Stage-2 baseline.
# Only the future trajectory is reoptimized. This preserves the matching
# accounting history without reproducing hundreds of rounded baseline values.
subject to Monthly_Renewable_Matching:
      sum {t in T: t < TAU_ACTIVE}
        (BASE_PV[SCEN_ACTIVE,BASE_CASE,t] + BASE_WD[SCEN_ACTIVE,BASE_CASE,t])*dt
    + sum {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}
        (p_pv[t]+p_wd[t])*dt
    >= MATCH_MONTHLY*MATCH_FRACTION *
      ( sum {t in T: t < TAU_ACTIVE}
          BASE_MATCH_LOAD[SCEN_ACTIVE,BASE_CASE,t]*dt
        + sum {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}
          p_match_load[t]*dt );

subject to Weekly_Renewable_Matching
  {w in W:
     (w-1)*WEEK_HOURS+1 <= NPER[SCEN_ACTIVE]
     and (if w*WEEK_HOURS <= NPER[SCEN_ACTIVE]
          then w*WEEK_HOURS else NPER[SCEN_ACTIVE]) >= TAU_ACTIVE}:

      sum {t in T:
          t < TAU_ACTIVE
          and t >= (w-1)*WEEK_HOURS+1
          and t <= (if w*WEEK_HOURS <= NPER[SCEN_ACTIVE]
                    then w*WEEK_HOURS else NPER[SCEN_ACTIVE])}
        (BASE_PV[SCEN_ACTIVE,BASE_CASE,t] + BASE_WD[SCEN_ACTIVE,BASE_CASE,t])*dt
    + sum {t in T:
          t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]
          and t >= (w-1)*WEEK_HOURS+1
          and t <= (if w*WEEK_HOURS <= NPER[SCEN_ACTIVE]
                    then w*WEEK_HOURS else NPER[SCEN_ACTIVE])}
        (p_pv[t]+p_wd[t])*dt
    >= MATCH_WEEKLY*MATCH_FRACTION *
      ( sum {t in T:
          t < TAU_ACTIVE
          and t >= (w-1)*WEEK_HOURS+1
          and t <= (if w*WEEK_HOURS <= NPER[SCEN_ACTIVE]
                    then w*WEEK_HOURS else NPER[SCEN_ACTIVE])}
          BASE_MATCH_LOAD[SCEN_ACTIVE,BASE_CASE,t]*dt
        + sum {t in T:
          t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]
          and t >= (w-1)*WEEK_HOURS+1
          and t <= (if w*WEEK_HOURS <= NPER[SCEN_ACTIVE]
                    then w*WEEK_HOURS else NPER[SCEN_ACTIVE])}
          p_match_load[t]*dt );

# Hourly matching is forward-looking from the activation instant; past hours
# have already occurred and cannot constrain a future activation request.
subject to Hourly_Renewable_Matching
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_pv[t]+p_wd[t]
    >= MATCH_HOURLY*MATCH_FRACTION*p_match_load[t];

# ============================================================
# Compressed pre-activation history
# ============================================================
# With the present plant model, the only dynamic physical state is H2 inventory.
# The cumulative NH3 already produced is also fixed so the remaining monthly
# production obligation is identical to the Stage-2 baseline.
subject to Activation_H2_State:
    h2_st[TAU_ACTIVE-1] = BASE_H2ST[SCEN_ACTIVE,BASE_CASE,TAU_ACTIVE-1];

subject to Prefix_NH3_History:
    sum {t in T: t < TAU_ACTIVE} nh3_prod[t]*dt
    = sum {t in T: t < TAU_ACTIVE} BASE_NH3[SCEN_ACTIVE,BASE_CASE,t]*dt;

# ============================================================
# Sustained activation request
# ============================================================
subject to Flex_Increase {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_p2a[t] >= BASE_P2A[SCEN_ACTIVE,BASE_CASE,t] + DeltaP
                 - M_POWER*(1-FLEX_INC*ACTIVE[t]);

subject to Flex_Decrease {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_p2a[t] <= BASE_P2A[SCEN_ACTIVE,BASE_CASE,t] - DeltaP
                 + M_POWER*(1-FLEX_DEC*ACTIVE[t]);

subject to Flex_Enable:
    DeltaP <= FLEX_DELTA_MAX*(FLEX_INC+FLEX_DEC);

subject to DeltaP_Lock_L:
    DeltaP >= DELTA_TARGET-EPS_DELTA-FLEX_DELTA_MAX*(1-LOCK_DELTA);
subject to DeltaP_Lock_U:
    DeltaP <= DELTA_TARGET+EPS_DELTA+FLEX_DELTA_MAX*(1-LOCK_DELTA);
