"""Local and reoptimized profile identifiability."""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import least_squares
from .core import bound_distance, log_bounds, predict, residuals

CHI2=3.841458820694124

def evaluate(rows, inventory, fit_result, *, profile_points=17):
    model=fit_result["model_id"]; best=fit_result["best"]; x=np.asarray(best["log_parameters"]); lo,hi=log_bounds(model)
    def raw(xx):
        p,_=predict(rows,inventory,model,xx)
        return np.asarray([math.log(p[(r.experiment_id,r.fraction_id,r.species_id)]/r.observed_kg_per_kg) for r in rows])
    h=1e-4; eye=np.eye(len(x)); jac=np.column_stack([(raw(x+h*eye[i])-raw(x-h*eye[i]))/(2*h) for i in range(len(x))])
    rank=int(np.linalg.matrix_rank(jac)); n=len(rows); dof=n-len(x); variance=float(np.dot(raw(x),raw(x))/dof)
    covariance=np.linalg.inv(jac.T@jac)*variance if rank==len(x) else np.full((len(x),len(x)),np.nan)
    se=np.sqrt(np.diag(covariance)); ci_lo=x-1.959963984540054*se;ci_hi=x+1.959963984540054*se
    threshold=best["objective"]+CHI2*variance
    names=["k_shared","Csat_shared"] if len(x)==2 else ["k_caffeine","Csat_caffeine","k_trigonelline","Csat_trigonelline"]
    traces=[]; classifications=[]
    for index,name in enumerate(names):
        grid=np.unique(np.concatenate((np.linspace(lo[index],x[index],profile_points),np.linspace(x[index],hi[index],profile_points))))
        for value in grid:
            mask=np.arange(len(x))!=index
            def fun(free):
                trial=x.copy();trial[index]=value;trial[mask]=free
                pred,_=predict(rows,inventory,model,trial);return residuals(rows,pred)
            sol=least_squares(fun,x[mask],bounds=(lo[mask],hi[mask]),xtol=1e-8,ftol=1e-8,gtol=1e-8,max_nfev=200)
            traces.append({"model_id":model,"parameter":name,"log_value":float(value),"physical_value":float(math.exp(value)),
              "objective":float(np.dot(sol.fun,sol.fun)),"threshold":float(threshold),"side":"lower" if value<x[index] else "upper" if value>x[index] else "optimum",
              "reoptimization_success":bool(sol.success),"free_log_parameters":";".join(map(str,sol.x))})
        own=[t for t in traces if t["parameter"]==name]
        lower_cross=any(t["side"]=="lower" and t["objective"]>=threshold for t in own)
        upper_cross=any(t["side"]=="upper" and t["objective"]>=threshold for t in own)
        physical=math.exp(x[index]);plo=math.exp(ci_lo[index]);phi=math.exp(ci_hi[index]);width=(phi-plo)/(2*physical)
        bname="k_1_s" if name.startswith("k") else "csat_kg_m3";bd=bound_distance(physical,bname)
        truncated=ci_lo[index]<=lo[index] or ci_hi[index]>=hi[index]
        classifications.append({"name":name,"fit":physical,"lower_95":plo,"upper_95":phi,"relative_95_half_width":width,
          "bound_distance":bd,"interval_truncated_by_bound":bool(truncated),"lower_profile_crossing":lower_cross,"upper_profile_crossing":upper_cross,
          "profile_open_to_bound":not(lower_cross and upper_cross),"identifiable":bool(width<=.25 and bd>.01 and not truncated and lower_cross and upper_cross)})
    modes=[]
    for candidate in fit_result["starts"]:
        if candidate["objective"]<=1.01*best["objective"]+1e-15 and np.linalg.norm(np.asarray(candidate["log_parameters"])-x)>.25:
            modes.append(candidate["start_index"])
    qualified=rank==len(x) and np.isfinite(covariance).all() and not modes and all(p["identifiable"] for p in classifications)
    return {"model_id":model,"finite_jacobian":bool(np.isfinite(jac).all()),"rank":rank,"columns":len(x),"finite_covariance":bool(np.isfinite(covariance).all()),
      "residual_variance":variance,"degrees_of_freedom":dof,"profile_threshold":threshold,"parameters":classifications,
      "material_near_optimal_modes":modes,"qualified":bool(qualified)},traces

