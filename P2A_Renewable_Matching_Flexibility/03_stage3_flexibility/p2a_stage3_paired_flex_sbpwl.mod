# ============================================================
# p2a_stage3_paired_flex_sbpwl.mod
# Stage 3 - paired PHYS-vs-RM activation-based flexibility
# Exact segment-binary PWL PEM model.
#
# FINAL STRUCTURE
# ---------------
# For each selected (scenario s, Stage-2 baseline case c,
# activation start tau, duration d, direction q):
#
#   PHYS : renewable matching is relaxed from tau onward.
#   RM   : the baseline temporal-matching rule remains enforced.
#
# Both branches start from the SAME Stage-2 state and accounting
# history. Only t >= tau is reoptimized. This future-only structure
# avoids recreating the already-realized prefix of the month.
#
# Stage-2 case IDs used here:
#   c=1 : monthly matching baseline
#   c=2 : hourly matching baseline
# The no-matching Stage-2 case is not paired because RM=PHYS there.
# ============================================================

set S ordered;
set CASES ordered;
set DURS ordered;

param TMAX integer > 0;
set T ordered := 1..TMAX;
set T0 ordered := 0..TMAX;
set N ordered;

param NPER {S} integer > 0, <= TMAX;
param PROB {S} >= 0, <= 1;
param dt > 0;

param zeta_PV {S,T} >= 0, <= 1 default 0;
param zeta_WD {S,T} >= 0, <= 1 default 0;

# ------------------------------------------------------------
# Fixed Stage-1 installation
# ------------------------------------------------------------
param P_PV_MAX > 0;
param P_WD_MAX > 0;
param H2_ST_MAX > 0;

# ------------------------------------------------------------
# Matching definition
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
param H2_STATE_REPLAY_TOL_KG >= 0;

# N2/NH3 subsystem
param LAMBDA_H2_NH3 > 0;
param LAMBDA_N2_NH3 > 0;
param N2_ASU_MAX > 0;
param N2_COMP_MAX > 0;
param SEC_ASU >= 0;
param SEC_N2_COMP >= 0;
param Q_NH3_MAX > 0;
param HB_MIN_LOAD >= 0, <= 1;
param NH3_REQ_FRAC >= HB_MIN_LOAD, <= 1;
param NH3_REPLAY_TOL_KG >= 0;
param SEC_HB >= 0;

# Grid parameters
param C_GRID >= 0;
param EPS_EXPORT >= 0;
param M_GRID > 0;
param M_POWER > 0;

# Flexibility numerics
param FLEX_DELTA_MAX > 0;
param FLEX_ZERO_TOL >= 0;
param BASE_REPLAY_TOL >= 0;

# ------------------------------------------------------------
# Reloaded Stage-2 baseline trajectories
# ------------------------------------------------------------
param BASE_P2A        {S,CASES,T} >= 0 default 0;
param BASE_PEL        {S,CASES,T} >= 0 default 0;
param BASE_H2PROD     {S,CASES,T} >= 0 default 0;
param BASE_NH3        {S,CASES,T} >= 0 default 0;
param BASE_PV         {S,CASES,T} >= 0 default 0;
param BASE_WD         {S,CASES,T} >= 0 default 0;
param BASE_MATCH_LOAD {S,CASES,T} >= 0 default 0;
param BASE_H2ST       {S,CASES,T0} >= 0 default 0;

# Prefix histories through hour k (k=0 means no elapsed hour).
param BASE_NH3_CUM   {S,CASES,T0} >= 0 default 0;
param BASE_RES_CUM   {S,CASES,T0} >= 0 default 0;
param BASE_MATCH_CUM {S,CASES,T0} >= 0 default 0;

# ------------------------------------------------------------
# Current activation selected by the run file
# ------------------------------------------------------------
param SCEN_ACTIVE in S default 1;
param BASE_CASE in CASES default 1;
param TAU_ACTIVE integer >= 1, <= TMAX default 1;
param DUR_ACTIVE in DURS default 1;
param FLEX_INC binary default 1;
param FLEX_DEC binary default 0;
check: FLEX_INC + FLEX_DEC = 1;
check: TAU_ACTIVE + DUR_ACTIVE - 1 <= NPER[SCEN_ACTIVE];

# ============================================================
# Variables - only the FUTURE t >= tau is instantiated
# ============================================================
var p_pv      {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_wd      {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_pv_curt {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_wd_curt {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;

var p_grid_imp {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_grid_exp {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var y_grid_import {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} binary;

var p_el_stack {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_el_seg {n in N, t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var y_seg    {n in N, t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} binary;
var h2_prod  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;

var p_bop     {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_h2_comp {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_asu     {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_n2_comp {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_hb      {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;

var h2_st {t in T0: t >= TAU_ACTIVE-1 and t <= NPER[SCEN_ACTIVE]} >= 0;
var h2_hb    {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var n2_prod  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var nh3_prod {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;

var p_p2a        {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;
var p_match_load {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]} >= 0;

# Guaranteed sustained deviation over the activation interval [MW].
var DeltaP >= 0, <= FLEX_DELTA_MAX;

# ============================================================
# Objective
# ============================================================
maximize FlexibilityAmplitude: DeltaP;

# ============================================================
# Renewable availability and electrical balance
# ============================================================
subject to PV_Availability
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_pv[t] + p_pv_curt[t] = P_PV_MAX*zeta_PV[SCEN_ACTIVE,t];

subject to WD_Availability
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_wd[t] + p_wd_curt[t] = P_WD_MAX*zeta_WD[SCEN_ACTIVE,t];

subject to PowerBalance
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_pv[t] + p_wd[t] + p_grid_imp[t] = p_p2a[t] + p_grid_exp[t];

# Prevent simultaneous import/export in a max-flexibility solve.
subject to Grid_Import_Mode
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_grid_imp[t] <= M_GRID*y_grid_import[t];

subject to Grid_Export_Mode
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_grid_exp[t] <= M_GRID*(1-y_grid_import[t]);

# ============================================================
# PEM electrolyzer - exact segment-binary PWL
# ============================================================
subject to EL_Power_Decomposition
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_el_stack[t] = sum {n in N} p_el_seg[n,t];

subject to EL_Segment_Lower
  {n in N, t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_el_seg[n,t] >= L[n]*P_EL_MAX*y_seg[n,t];

subject to EL_Segment_Upper
  {n in N, t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_el_seg[n,t] <= U[n]*P_EL_MAX*y_seg[n,t];

subject to EL_One_Segment
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    sum {n in N} y_seg[n,t] <= 1;

subject to EL_Stack_Capacity
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_el_stack[t] <= P_EL_MAX;

subject to H2_Production_PWL
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    h2_prod[t] = sum {n in N}
      (A[n]*p_el_seg[n,t] + B[n]*P_EL_MAX*y_seg[n,t]);

subject to BOP_Power
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_bop[t] = SEC_BOP*h2_prod[t];

# ============================================================
# H2 subsystem
# ============================================================
subject to H2_Compressor_Power
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_h2_comp[t] = SEC_H2_COMP*h2_prod[t];

subject to H2_Compressor_Capacity
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    h2_prod[t] <= H2_COMP_MAX;

subject to H2_Storage_Balance
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    h2_st[t] = h2_st[t-1] + dt*(h2_prod[t]-h2_hb[t]);

subject to H2_Storage_Lower
  {t in T0: t >= TAU_ACTIVE-1 and t <= NPER[SCEN_ACTIVE]}:
    h2_st[t] >= H2_ST_MIN_FRAC*H2_ST_MAX;

subject to H2_Storage_Upper
  {t in T0: t >= TAU_ACTIVE-1 and t <= NPER[SCEN_ACTIVE]}:
    h2_st[t] <= H2_ST_MAX_FRAC*H2_ST_MAX;

# Same physical state immediately before activation as Stage 2, with a
# sub-gram numerical replay band because the Stage-2 trajectory is reloaded
# from decimal CSV output.
subject to Activation_H2_State_Lower:
    h2_st[TAU_ACTIVE-1]
    >= BASE_H2ST[SCEN_ACTIVE,BASE_CASE,TAU_ACTIVE-1] - H2_STATE_REPLAY_TOL_KG;

subject to Activation_H2_State_Upper:
    h2_st[TAU_ACTIVE-1]
    <= BASE_H2ST[SCEN_ACTIVE,BASE_CASE,TAU_ACTIVE-1] + H2_STATE_REPLAY_TOL_KG;

# Restore the exact Stage-2 terminal target (50% of tank capacity), again
# using only the tiny numerical replay band.
subject to H2_Storage_Terminal_Lower:
    h2_st[NPER[SCEN_ACTIVE]]
    >= H2_ST_INIT_FRAC*H2_ST_MAX - H2_STATE_REPLAY_TOL_KG;

subject to H2_Storage_Terminal_Upper:
    h2_st[NPER[SCEN_ACTIVE]]
    <= H2_ST_INIT_FRAC*H2_ST_MAX + H2_STATE_REPLAY_TOL_KG;

# ============================================================
# N2 / NH3 subsystem
# ============================================================
subject to H2_to_HB
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    h2_hb[t] = LAMBDA_H2_NH3*nh3_prod[t];

subject to N2_to_HB
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    n2_prod[t] = LAMBDA_N2_NH3*nh3_prod[t];

subject to ASU_Capacity
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    n2_prod[t] <= N2_ASU_MAX;

subject to N2_Compressor_Capacity
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    n2_prod[t] <= N2_COMP_MAX;

subject to ASU_Power
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_asu[t] = SEC_ASU*n2_prod[t];

subject to N2_Compressor_Power
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_n2_comp[t] = SEC_N2_COMP*n2_prod[t];

subject to HB_Minimum_Load
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    nh3_prod[t] >= HB_MIN_LOAD*Q_NH3_MAX;

subject to HB_Maximum_Load
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    nh3_prod[t] <= Q_NH3_MAX;

subject to HB_Power
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_hb[t] = SEC_HB*nh3_prod[t];

# Preserve the exact Stage-2 monthly NH3 target.  The already-realized
# prefix is reloaded from Stage 2, so a sub-gram replay band is used only
# to absorb decimal I/O roundoff.
subject to Monthly_NH3_Requirement_Lower:
      BASE_NH3_CUM[SCEN_ACTIVE,BASE_CASE,TAU_ACTIVE-1]
    + sum {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}
        nh3_prod[t]*dt
    >= NH3_REQ_FRAC*Q_NH3_MAX*NPER[SCEN_ACTIVE]*dt - NH3_REPLAY_TOL_KG;

subject to Monthly_NH3_Requirement_Upper:
      BASE_NH3_CUM[SCEN_ACTIVE,BASE_CASE,TAU_ACTIVE-1]
    + sum {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}
        nh3_prod[t]*dt
    <= NH3_REQ_FRAC*Q_NH3_MAX*NPER[SCEN_ACTIVE]*dt + NH3_REPLAY_TOL_KG;

subject to Total_P2A_Power
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_p2a[t] = p_el_stack[t] + p_bop[t] + p_h2_comp[t]
             + p_asu[t] + p_n2_comp[t] + p_hb[t];

# ============================================================
# Renewable matching
# ============================================================
subject to Matching_Load_Definition
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_match_load[t]
    = (1-MATCH_FULL_P2A)*(p_el_stack[t]+p_bop[t])
      + MATCH_FULL_P2A*p_p2a[t];

# For monthly RM, the realized Stage-2 prefix is retained in the
# accounting balance and only the future is reoptimized.
subject to Monthly_Renewable_Matching:
      BASE_RES_CUM[SCEN_ACTIVE,BASE_CASE,TAU_ACTIVE-1]
    + sum {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}
        (p_pv[t]+p_wd[t])*dt
    >= MATCH_MONTHLY*MATCH_FRACTION *
      ( BASE_MATCH_CUM[SCEN_ACTIVE,BASE_CASE,TAU_ACTIVE-1]
        + sum {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}
            p_match_load[t]*dt );

# For hourly RM, matching is enforced at every future hour.
subject to Hourly_Renewable_Matching
  {t in T: t >= TAU_ACTIVE and t <= NPER[SCEN_ACTIVE]}:
    p_pv[t] + p_wd[t]
    >= MATCH_HOURLY*MATCH_FRACTION*p_match_load[t];

# ============================================================
# Sustained activation request
# ============================================================
# INC and DEC use inequalities, so DeltaP is the guaranteed sustained
# deviation; overshoot is permitted within the activation interval.
subject to Flex_Increase
  {t in T: t >= TAU_ACTIVE and t <= TAU_ACTIVE+DUR_ACTIVE-1}:
    p_p2a[t] >= BASE_P2A[SCEN_ACTIVE,BASE_CASE,t]
                + DeltaP - BASE_REPLAY_TOL
                - M_POWER*(1-FLEX_INC);

subject to Flex_Decrease
  {t in T: t >= TAU_ACTIVE and t <= TAU_ACTIVE+DUR_ACTIVE-1}:
    p_p2a[t] <= BASE_P2A[SCEN_ACTIVE,BASE_CASE,t]
                - DeltaP + BASE_REPLAY_TOL
                + M_POWER*(1-FLEX_DEC);

