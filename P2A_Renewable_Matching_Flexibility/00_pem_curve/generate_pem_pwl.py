#!/usr/bin/env python3
"""Regenerate the nonlinear PEM curve and optimal endpoint-interpolating PWL model.

The implementation is a script version of the supplied PEM notebook. It:
  1) evaluates the nonlinear electrochemical PEM model;
  2) constructs h(x)=m_H2(x)/P_EL,max on x in [0.15, 1.00];
  3) creates 1000 uniformly spaced candidate points;
  4) computes the SSE of every endpoint-interpolating candidate chord;
  5) uses dynamic programming to select the globally minimum-SSE breakpoint
     subset for a fixed number of segments within that 1000-point grid;
  6) writes optimization-ready AMPL coefficients and audit tables.

The paper workflow adopts six PWL segments. Other segment counts are evaluated
only to document the fidelity/complexity trade-off; there is no automatic model-
selection criterion in this script.
"""
from __future__ import annotations

from pathlib import Path
import argparse, csv, json
import numpy as np

# -----------------------------------------------------------------------------
# Nonlinear PEM model parameters from the supplied notebook
# -----------------------------------------------------------------------------
R = 8.314
F_CONST = 96485.0
M_H2 = 2.01588e-3
T_CELL = 60.0
T_STD = 298.15
P_CAT = 30.0
P_AN = 30.0
I_MAX = 2.0e4
I_LIM = 3.0e5
C_E = 94.7
A_CELL = 0.2
V_RATED_REFERENCE = 2.04
H2_RATED_REFERENCE = 1765.0

ALPHA_CAT = 0.302
ALPHA_AN = 0.676
I0_REF_CAT = 52.0
I0_REF_AN = 3.0e-4
E_ACT_CAT = 8.96e3
E_ACT_AN = 60.0e3
PHI_I_CAT = 0.75
PHI_I_AN = 0.75
M_M_CAT = 0.3e-2
M_M_AN = 1.0e-2
RHO_M_CAT = 21.45e3
RHO_M_AN = 22.65e3
D_M_CAT = 2.7e-9
D_M_AN = 2.9e-9
SIGMA_MEM_REF = 100.9
E_ACT_MEM = 9.91e3
DELTA_MEM = 1.83e-4
ASR_ELEC_CM2 = 0.1048
ASR_ELEC = ASR_ELEC_CM2 * 1e-4
A_F = -0.1037
B_F = -1.0
C_F = 1.0

X_MIN = 0.15
X_MAX = 1.00
N_DENSE = 50000
N_MASTER = 1000
DEFAULT_SEGMENTS = 6
SEGMENT_LIST = (3, 5, 6, 9, 12, 15)


def p_h2o(t_c):
    return (610.0 / 1e5) * np.exp(17.2694 * t_c / (t_c + 238.3))


def e0(t_k):
    return 1.229 - 0.9e-3 * (t_k - T_STD)


def v_rev(t_c, p_cat, p_an):
    t_k = t_c + 273.15
    p_water = p_h2o(t_c)
    return e0(t_k) + R*t_k/(2.0*F_CONST) * np.log(((p_cat-p_water)*np.sqrt(p_an-p_water))/p_water)


def gamma_m(phi_i, m_m, rho_m, d_m):
    return phi_i*m_m*6.0/(rho_m*d_m)


GAMMA_CAT = gamma_m(PHI_I_CAT, M_M_CAT, RHO_M_CAT, D_M_CAT)
GAMMA_AN = gamma_m(PHI_I_AN, M_M_AN, RHO_M_AN, D_M_AN)


def i0_exchange(t_k, gamma, i0_ref, e_act):
    return gamma*i0_ref*np.exp(-(e_act/R)*(1.0/t_k - 1.0/T_STD))


def theta_bubble(t_k, i):
    return (-97.25 + 182.0*(t_k/T_STD) - 84.0*(t_k/T_STD)**2) * (i/I_LIM)**0.3


def v_act(t_c, i):
    t_k=t_c+273.15
    theta=theta_bubble(t_k,i)
    i0_cat=i0_exchange(t_k,GAMMA_CAT,I0_REF_CAT,E_ACT_CAT)
    i0_an=i0_exchange(t_k,GAMMA_AN,I0_REF_AN,E_ACT_AN)
    return ((R*t_k/(ALPHA_CAT*F_CONST))*np.arcsinh(i/(2.0*i0_cat*(1.0-theta)))
            +(R*t_k/(ALPHA_AN*F_CONST))*np.arcsinh(i/(2.0*i0_an*(1.0-theta))))


def sigma_mem(t_k):
    return SIGMA_MEM_REF*np.exp(-(E_ACT_MEM/R)*(1.0/t_k - 1.0/T_STD))


def asr_eq(t_k):
    return ASR_ELEC + DELTA_MEM/sigma_mem(t_k)


def v_ohm(t_c,i):
    return asr_eq(t_c+273.15)*i


def v_diff(t_c,i):
    t_k=t_c+273.15
    return (R*t_k/(4.0*F_CONST))*np.log(1.0-i/I_LIM)


def v_cell(t_c,p_cat,p_an,i):
    return v_rev(t_c,p_cat,p_an)+v_act(t_c,i)+v_ohm(t_c,i)+v_diff(t_c,i)


def eta_f(i):
    return A_F*i**B_F + C_F


def n_cell(i_max,a_cell,c_e,t_c,p_cat,p_an):
    i_max_cell=i_max*a_cell
    v_max_cell=v_cell(t_c,p_cat,p_an,i_max)
    return c_e*1e6/(i_max_cell*v_max_cell)


def h2_production(i,a_cell,n_c):
    n_h2_mol_s=eta_f(i)*n_c*i*a_cell/(2.0*F_CONST)
    return n_h2_mol_s*M_H2*3600.0


def stack_power(t_c,p_cat,p_an,i,a_cell,n_c):
    return v_cell(t_c,p_cat,p_an,i)*i*a_cell*n_c/1e6


def build_master_curve():
    n_c=n_cell(I_MAX,A_CELL,C_E,T_CELL,P_CAT,P_AN)
    i_dense=np.linspace(1.0,I_MAX,N_DENSE)
    p_dense=stack_power(T_CELL,P_CAT,P_AN,i_dense,A_CELL,n_c)
    p_max=stack_power(T_CELL,P_CAT,P_AN,I_MAX,A_CELL,n_c)
    h2_max=h2_production(I_MAX,A_CELL,n_c)
    x_dense=p_dense/p_max
    if not np.all(np.diff(x_dense)>0):
        raise RuntimeError('Normalized PEM power is not strictly increasing with current density.')
    x=np.linspace(X_MIN,X_MAX,N_MASTER)
    i_x=np.interp(x,x_dense,i_dense)
    h2=h2_production(i_x,A_CELL,n_c)
    h=h2/p_max
    return n_c,p_max,h2_max,x,h


def build_chord_error_matrix(x,h):
    n=len(x)
    prefix_x=np.concatenate(([0.0],np.cumsum(x)))
    prefix_x2=np.concatenate(([0.0],np.cumsum(x*x)))
    prefix_h=np.concatenate(([0.0],np.cumsum(h)))
    prefix_h2=np.concatenate(([0.0],np.cumsum(h*h)))
    prefix_xh=np.concatenate(([0.0],np.cumsum(x*h)))
    err=np.full((n,n),np.inf)
    for i in range(n-1):
        j=np.arange(i+1,n)
        a=(h[j]-h[i])/(x[j]-x[i])
        b=h[i]-a*x[i]
        nn=(j-i+1).astype(float)
        sx=prefix_x[j+1]-prefix_x[i]
        sx2=prefix_x2[j+1]-prefix_x2[i]
        sh=prefix_h[j+1]-prefix_h[i]
        sh2=prefix_h2[j+1]-prefix_h2[i]
        sxh=prefix_xh[j+1]-prefix_xh[i]
        sse=sh2+a*a*sx2+b*b*nn-2*a*sxh-2*b*sh+2*a*b*sx
        err[i,j]=np.maximum(sse,0.0)
    return err


def dynamic_programming(x,h,err,segment_list):
    n=len(x); max_segments=max(segment_list)
    cost=np.full((max_segments+1,n),np.inf)
    prev=np.full((max_segments+1,n),-1,dtype=int)
    cost[1,1:]=err[0,1:]
    for k in range(2,max_segments+1):
        for j in range(k,n):
            ii=np.arange(k-1,j)
            cc=cost[k-1,ii]+err[ii,j]
            pos=int(np.argmin(cc))
            cost[k,j]=cc[pos]; prev[k,j]=ii[pos]
    results={}
    for s in segment_list:
        j=n-1; idx=[j]
        for k in range(s,1,-1):
            j=prev[k,j]
            if j<0: raise RuntimeError('DP backtracking failed')
            idx.append(j)
        idx.append(0); idx=np.array(sorted(idx),dtype=int)
        xb=x[idx]; hb=h[idx]
        a=(hb[1:]-hb[:-1])/(xb[1:]-xb[:-1])
        b=hb[:-1]-a*xb[:-1]
        results[s]={'idx':idx,'x':xb,'h':hb,'A':a,'B':b,'SSE':float(cost[s,n-1])}
    return results


def eval_pwl(x,r):
    seg=np.searchsorted(r['x'][1:-1],x,side='right')
    return r['A'][seg]*x+r['B'][seg]


def metrics(x,h,r):
    approx=eval_pwl(x,r); e=h-approx
    rmse=float(np.sqrt(np.mean(e*e))); mae=float(np.mean(np.abs(e))); mx=float(np.max(np.abs(e)))
    return {'SSE':float(np.sum(e*e)),'RMSE_kg_per_MWh':rmse,'MAE_kg_per_MWh':mae,
            'max_abs_error_kg_per_MWh':mx,'RMSE_percent_of_rated_h':100*rmse/h[-1],
            'max_error_percent_of_rated_h':100*mx/h[-1],
            'min_nonlinear_minus_pwl_kg_per_MWh':float(np.min(e)),
            'overestimating_master_points':int(np.sum(e < -1e-10))}


def write_outputs(out:Path, selected:int):
    out.mkdir(parents=True,exist_ok=True)
    n_c,p_max,h2_max,x,h=build_master_curve()
    err=build_chord_error_matrix(x,h)
    segs=tuple(sorted(set(SEGMENT_LIST+(selected,))))
    res=dynamic_programming(x,h,err,segs)
    mets={s:metrics(x,h,res[s]) for s in segs}

    # Master nonlinear curve
    with (out/'pem_master_curve.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['x_pu','h_kg_per_MWh','power_MW','h2_kg_per_h','efficiency_kg_per_MWh'])
        for xx,hh in zip(x,h):
            power=xx*p_max; h2=hh*p_max; w.writerow([f'{xx:.12f}',f'{hh:.12f}',f'{power:.12f}',f'{h2:.12f}',f'{h2/power:.12f}'])

    # Metrics across alternative segment counts
    with (out/'pem_pwl_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['segments','breakpoints','SSE','RMSE_kg_per_MWh','MAE_kg_per_MWh','max_abs_error_kg_per_MWh','RMSE_percent_of_rated_h','max_error_percent_of_rated_h','min_nonlinear_minus_pwl_kg_per_MWh','overestimating_master_points']
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for s in segs:
            row={'segments':s,'breakpoints':' '.join(f'{v:.8f}' for v in res[s]['x']),**mets[s]}; w.writerow(row)

    # All coefficients
    with (out/'pem_pwl_coefficients_all.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['segments','segment','L_pu','U_pu','A_kg_per_MWh','B_kg_per_MWh'])
        for s in segs:
            r=res[s]
            for n,(lo,hi,a,b) in enumerate(zip(r['x'][:-1],r['x'][1:],r['A'],r['B']),1):
                w.writerow([s,n,f'{lo:.12f}',f'{hi:.12f}',f'{a:.12f}',f'{b:.12f}'])

    r=res[selected]; m=mets[selected]
    with (out/f'pem_pwl_{selected}segments.dat').open('w',encoding='utf-8') as f:
        f.write('# AUTO-GENERATED by 00_pem_curve/generate_pem_pwl.py; do not edit by hand.\n')
        f.write(f'# PEM: {T_CELL:.1f} C, {P_CAT:.1f}/{P_AN:.1f} bar, Pmax={p_max:.6f} MW.\n')
        f.write(f'# DP: {N_MASTER} uniform candidate points on [{X_MIN:.2f},{X_MAX:.2f}] p.u.; objective = total chord SSE.\n')
        f.write(f'# Selected segments={selected}; RMSE={m["RMSE_kg_per_MWh"]:.12g} kg/MWh; max error={m["max_abs_error_kg_per_MWh"]:.12g} kg/MWh.\n')
        f.write('data;\n\n')
        f.write('set N := '+' '.join(str(i) for i in range(1,selected+1))+';\n\n')
        f.write('param: L        U        A             B :=\n')
        for n,(lo,hi,a,b) in enumerate(zip(r['x'][:-1],r['x'][1:],r['A'],r['B']),1):
            f.write(f'{n:<2d}     {lo:.5f}  {hi:.5f}  {a:.8f}   {b:.8f}\n')
        f.write(';\n')

    summary={
        'pem_model':{'temperature_C':T_CELL,'cathode_pressure_bar':P_CAT,'anode_pressure_bar':P_AN,
                     'rated_power_MW':p_max,'rated_h2_model_kg_per_h':h2_max,'rated_voltage_reference_V':V_RATED_REFERENCE,
                     'h2_reference_kg_per_h':H2_RATED_REFERENCE,'number_of_cells':n_c},
        'pwl':{'productive_domain_pu':[X_MIN,X_MAX],'candidate_points':N_MASTER,'dense_inversion_points':N_DENSE,
               'selected_segments':selected,'alternative_segments':list(segs),'breakpoints_pu':[float(v) for v in r['x']],
               'metrics':m}
    }
    (out/'pem_pwl_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary


def main():
    ap=argparse.ArgumentParser(description='Regenerate PEM nonlinear curve and DP PWL coefficients.')
    ap.add_argument('--segments',type=int,default=DEFAULT_SEGMENTS)
    ap.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent/'generated')
    a=ap.parse_args()
    if a.segments<1: raise SystemExit('--segments must be positive')
    s=write_outputs(a.output_dir,a.segments)
    p=s['pwl']; print('PEM/PWL preprocessing complete')
    print(f'  selected segments: {p["selected_segments"]}')
    print('  breakpoints:', ', '.join(f'{v:.5f}' for v in p['breakpoints_pu']))
    print(f'  RMSE: {p["metrics"]["RMSE_kg_per_MWh"]:.12f} kg/MWh')
    print(f'  max abs error: {p["metrics"]["max_abs_error_kg_per_MWh"]:.12f} kg/MWh')
    print(f'  outputs: {a.output_dir}')

if __name__=='__main__': main()
