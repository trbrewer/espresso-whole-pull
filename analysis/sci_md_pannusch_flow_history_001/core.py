"""Chemistry-blind, fail-closed flow semantics and clock qualification.

Source-derived facts remain CC-BY-NC-3.0 and are not relicensed as code.
"""
from __future__ import annotations
import hashlib, json, math, pathlib

TASK = "SCI-MD-PANNUSCH-FLOW-HISTORY-001"
PRIMARY = ("PRED-C01", "PRED-C02", "PRED-C05", "PRED-C06")
RAMP = ("PRED-C07", "PRED-C08")
EXCLUDED = ("PRED-C03", "PRED-C04")
ASSAY_IDS = (1, 2, 3, 5, 7, 10)
RIGHTS = "CC-BY-NC-3.0; source-derived numeric data are not relicensed as repository code"
REQUIRED_CLAIMS = ("TARGET_EXPOSED", "SOURCE_INTERNAL", "NOT INDEPENDENT VALIDATION",
                   "NOT PHYSICAL VALIDATION", "NOT HYDRAULIC VALIDATION",
                   "NOT PUCK_FACE_FLOW VALIDATION", "NOT PRODUCTION QUALIFICATION")
EXPECTED = {
 "ExperimentalData_validation.mat":"b5fb0245e5cb67cf3191127f6058624243a38fc0031344f8c93344bb95a84d64",
 "MassData_modelval.mat":"430f922d0df443d9f1b1d629409d9ef4a4967d15535ffa8b5a34f795523faaf3",
 "DesignOfExperiments_Validation_03_22.xlsx":"b7fc864e693ddb40317a4c9493a2fb0c0892b1f1c68f5ce581d48008e21cab57",
 "getExperimentalData_validation.m":"b1a219b851887af69611a9f22c810c7c07f1f3b8e714e6d4ef62500c960deee7",
 "GetMassScale_modelval.m":"9d354ae2fd10148b926e4a5fc9adeafa99ced15d0f24a1a99324a3c81de44b56",
 "ReadMassTimeFromScale.m":"12958952f478afd13387c842e6290ca7551d2511526c6f488a0081a11506192e"}

def sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def canonical(value): return (json.dumps(value,indent=2,sort_keys=True)+"\n").encode()

def qualify_candidate(*, units, physical_side, clock_zero, support, conversion=None,
                      published_q_role=False, fitted_adjustment=False, extrapolation=False):
    reasons=[]
    if not units: reasons.append("MISSING_UNITS")
    if physical_side not in {"MODEL_Q_EXPLICIT", "PROGRAMMED_MACHINE_INSTRUCTION"}: reasons.append("AMBIGUOUS_OR_INADMISSIBLE_PHYSICAL_SIDE")
    if clock_zero is None: reasons.append("MISSING_CLOCK_ZERO")
    if support is None: reasons.append("MISSING_SUPPORT")
    if units in {"g/s","kg/s"} and not conversion: reasons.append("MISSING_MASS_TO_VOLUME_CONVERSION")
    if not published_q_role: reasons.append("NO_PUBLISHED_PANNUSCH_Q_MAPPING")
    if fitted_adjustment: reasons.append("FITTED_LAG_OFFSET_OR_MULTIPLIER_PROHIBITED")
    if extrapolation: reasons.append("UNSUPPORTED_EXTRAPOLATION_PROHIBITED")
    return ("ELIGIBLE" if not reasons else "INELIGIBLE", reasons)

def validate_q(q, points):
    values=[float(q(t)) for t in points]
    if not values or any(not math.isfinite(x) or x <= 0 for x in values):
        raise ValueError("q(t) must be finite and strictly positive on full support")
    return values

def candidate_registry(_chemistry=None):
    """Construction deliberately ignores chemistry; ordering is source-declared."""
    return [
      {"candidate_id":"Q0_LEGACY_CONSTANT_START","source_semantic":"PROGRAMMED_MACHINE_INSTRUCTION_NOT_MEASURED_INLET_OR_PUCK_FACE_FLOW","formula":"q(t)=flow_start_mL_s","units":"mL/s","clock":"solver elapsed seconds","support":"all solver intervals","pre_support_behaviour":"not applicable","post_support_behaviour":"not applicable","applicable_conditions":list(PRIMARY+RAMP),"source_evidence":"Puckworks prediction_conditions.csv","eligibility":"ELIGIBLE_BASELINE_ONLY","reason":"mandatory existing scalar-start baseline; no fitted parameters","primary_or_diagnostic_role":"mandatory baseline","target_independent_construction_proof":"literal source start value; chemistry argument ignored"},
      {"candidate_id":"QP_SOURCE_PROGRAMMED_SCHEDULE","source_semantic":"SOURCE_PROGRAMMED_MACHINE_SCHEDULE_NOT_MEASURED_INLET_FLOW","formula":"source exact schedule only; no generic endpoint interpolation","units":"mL/s","clock":"UNRESOLVED_PROGRAMME_TO_SOLVER","support":"UNRESOLVED_FOR_RAMPS","pre_support_behaviour":"UNRESOLVED","post_support_behaviour":"UNRESOLVED","applicable_conditions":list(PRIMARY+RAMP),"source_evidence":"workbook DoE endpoint labels; no time-coordinate cells or released programme definition","eligibility":"INELIGIBLE_NONIDENTITY;IDENTICAL_TO_Q0_ON_PRIMARY","reason":"ramp coordinate, zero, support, duration, and pre/post holds absent","primary_or_diagnostic_role":"gated source schedule","target_independent_construction_proof":"static source metadata only"},
      {"candidate_id":"QP_VOLUME_EQUIVALENT_CONSTANT","source_semantic":"DIAGNOSTIC_DERIVED_FROM_QP","formula":"constant integral-equivalent QP over exact solver support","units":"mL/s","clock":"solver elapsed seconds","support":"NOT_CONSTRUCTED","pre_support_behaviour":"not applicable","post_support_behaviour":"not applicable","applicable_conditions":list(RAMP),"source_evidence":"requires eligible QP","eligibility":"GATED_INELIGIBLE","reason":"QP is ineligible; diagnostic must not be constructed","primary_or_diagnostic_role":"diagnostic only","target_independent_construction_proof":"would use QP integral only"},
      {"candidate_id":"QM_MASSDATA_FLOW_SCALAR","source_semantic":"MISNAMED_REGISTRY_ENTRY_SOURCE_OBJECT_IS_VECTOR","formula":"exact MassData.flow if source-authorized","units":"g/s (dm/dt stored without density conversion)","clock":"rebased scale mass-fit seconds","support":"MassData.time fit support","pre_support_behaviour":"undefined","post_support_behaviour":"undefined","applicable_conditions":list(PRIMARY+RAMP),"source_evidence":"GetMassScale_modelval.m: dm_dt=2*a*tfit+b; flow=dm_dt; MassData.flow=flow","eligibility":"INELIGIBLE","reason":"not scalar; beverage mass-rate physical side; no volumetric conversion or published Pannusch-Q authorization","primary_or_diagnostic_role":"gated input mapping","target_independent_construction_proof":"released mass-scale code only"},
      {"candidate_id":"QD_MASS_DERIVATIVE_OUTFLOW","source_semantic":"BEVERAGE_MASS_DERIVED_OUTFLOW_TIMING;DERIVED_NOT_INLET_FLOW;CONTEXT_ONLY","formula":"dm/dt=2*a*t+b","units":"g/s","clock":"rebased scale mass-fit seconds","support":"MassData.time fit support","pre_support_behaviour":"undefined","post_support_behaviour":"undefined","applicable_conditions":list(PRIMARY+RAMP),"source_evidence":"GetMassScale_modelval.m and getExperimentalData_validation.m","eligibility":"GATED_INELIGIBLE_BY_CURRENT_AUTHORITY","reason":"beverage outflow is not inlet Q; density/conversion and programme/solver clock mapping unauthorized; no published Pannusch-Q use","primary_or_diagnostic_role":"context only","target_independent_construction_proof":"released mass-scale code only"}]

def classify_overall(registry):
    nonidentity=[r for r in registry if r["candidate_id"]!="Q0_LEGACY_CONSTANT_START"]
    if any(r["eligibility"]=="ELIGIBLE" for r in nonidentity): raise ValueError("scoring required")
    return "SCI_MD_PANNUSCH_FLOW_HISTORY_001_FLOW_AUTHORITY_INELIGIBLE"

