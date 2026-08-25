"""Application-specific reduced numerical qualification."""
from __future__ import annotations
import math
import numpy as np
from .core import predict

def qualify(rows, inventory, model, log_parameters):
    reference,diag=predict(rows,inventory,model,log_parameters,cells=32,dt_s=.1)
    repeat,_=predict(rows,inventory,model,log_parameters,cells=32,dt_s=.1)
    spatial,_=predict(rows,inventory,model,log_parameters,cells=64,dt_s=.1)
    temporal,_=predict(rows,inventory,model,log_parameters,cells=32,dt_s=.05)
    keys=sorted(reference)
    def nrmse(other):
        a=np.asarray([reference[k] for k in keys]);b=np.asarray([other[k] for k in keys]);return float(np.sqrt(np.mean((a-b)**2))/np.mean(a))
    conservation=max(abs(d["conservation_residual_kg"]) for d in diag.values())
    bounded=all(d["remaining_inventory_kg"]>=0 and d["dissolved_mass_kg"]>=0 and math.isfinite(d["cup_mass_kg"]) for d in diag.values())
    metrics={"deterministic_exact":reference==repeat,"maximum_conservation_residual_kg":conservation,"nonnegative_finite_state":bounded,
      "spatial_refinement_nrmse":nrmse(spatial),"time_refinement_nrmse":nrmse(temporal),"fraction_boundary_operator":"linear cumulative-cup interpolation at exact frozen mass boundaries",
      "source_cap":"inherited canonical adapter beginning-step min(source, remaining/dt)","production_reference_fine":"REQUIRES_POSTFIT_FULL_PARITY",
      "serial_parallel":"inherited Stage-C V12 by executable/source hash; application-specific confirmation required if full application becomes representable"}
    metrics["reduced_pass"]=metrics["deterministic_exact"] and bounded and conservation<=1e-12 and metrics["spatial_refinement_nrmse"]<=.01 and metrics["time_refinement_nrmse"]<=.01
    return metrics
