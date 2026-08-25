"""Target-blind reduced/full application parity controls."""
from __future__ import annotations
import json
from pathlib import Path
from .core import BOUNDS, DIFFUSIVITY, sha256

PRODUCTION_SOURCE_SHA="9ffba0fa7800de50375a2a0c94cf99127870ac4451b104866c7e50322c992599"
EXECUTABLE_SHA="d793a731fd2f4f82e623350c61835d0e955d886849f5e363a5abd8dd0fae4c93"

def frozen_matrix(observations, inventories):
    flows=sorted({r.flow_m3_s for r in observations}); schedules=sorted({r.upper_mass_kg for r in observations})
    ks=(BOUNDS["k_1_s"][0],(.002*.5)**.5,BOUNDS["k_1_s"][1])
    cs=(BOUNDS["csat_kg_m3"][0],(.2*100.)**.5,BOUNDS["csat_kg_m3"][1])
    inv=sorted(inventories.values())
    return {"selection":"TARGET_BLIND_LOW_INTERIOR_HIGH","k_1_s":ks,"csat_kg_m3":cs,
      "diffusivity_m2_s":DIFFUSIVITY,"flow_m3_s":(flows[0],flows[len(flows)//2],flows[-1]),
      "fraction_endpoint_mass_kg":(schedules[0],schedules[len(schedules)//2],schedules[-1]),
      "inventory_mass_fraction_range":(inv[0],inv[-1]),"geometry":{"length_m":.015,"diameter_m":.058,"porosity":.17},
      "thresholds":{"species_prediction_nrmse_max":.01,"endpoint_cup_mass_relative_discrepancy_max":.005}}

def prefit_qualification(root: Path, executable: Path, matrix: dict) -> dict:
    """Fail before simulation when identical prescribed-flow application is absent."""
    source=root/"solver/espressoWholePullFoam/espressoWholePullFoam.C"
    prepare=(root/"scripts/prepare_case.py").read_text(encoding="utf-8")
    result={"stage":"TARGET_BLIND_PREFIT","matrix":matrix,"production_source_sha256":sha256(source),
      "executable_identity":"accepted Stage-C final-build executable","executable_sha256":sha256(executable) if executable.is_file() else None,
      "accepted_stage_c_harness":"tools.sci_md_004_stage_c.runner.Matrix.run",
      "required_application":"fixed prescribed volumetric flow for complete fraction schedule",
      "supported_boundary_models":["prescribedPressure","lumpedMachine"],"optimizer_call_count":0}
    immutable=result["production_source_sha256"]==PRODUCTION_SOURCE_SHA
    executable_ok=result["executable_sha256"]==EXECUTABLE_SHA
    has_flow_boundary="prescribedFlow" in prepare
    result.update({"production_source_immutable":immutable,"accepted_executable":executable_ok,
      "identical_prescribed_flow_representable":has_flow_boundary})
    if not immutable or not executable_ok:
        result.update({"status":"FAIL","reason":"IMMUTABLE_PRODUCTION_AUTHORITY_MISMATCH","pass":False})
    elif not has_flow_boundary:
        result.update({"status":"CONTRACT_BLOCKED","reason":"UNCHANGED_PRODUCTION_INTERFACE_HAS_NO_IDENTICAL_PRESCRIBED_FLOW_BOUNDARY","pass":False})
    else:
        result.update({"status":"READY_FOR_TARGET_BLIND_MATRIX_EXECUTION","reason":None,"pass":False})
    return result
