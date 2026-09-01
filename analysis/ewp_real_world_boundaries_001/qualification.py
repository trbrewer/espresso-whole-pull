from __future__ import annotations

import math
from collections import Counter

from .corpus_adapter import AdaptedRecord


FLAGS = ("boundary_summary_eligible", "commanded_pressure_profile_eligible", "achieved_pressure_profile_eligible",
         "pressure_tracking_eligible", "scale_mass_profile_eligible", "scale_flow_profile_eligible",
         "pressure_flow_context_eligible", "ewp_pressure_boundary_executable", "library_only_eligible")


def qualify(r: AdaptedRecord) -> tuple[dict[str, bool], set[str]]:
    reasons: set[str] = set()
    n = len(r.time_s)
    if r.schema_version != 6: reasons.add("UNSUPPORTED_STORE_SCHEMA")
    if not n: reasons.add("MISSING_TIME")
    if any(x is None or not math.isfinite(x) for x in r.time_s): reasons.add("NONFINITE_TIME")
    lengths = [len(x) for x in (r.achieved_pressure_pa, r.commanded_pressure_pa, r.scale_flow_kg_s,
                                r.cumulative_scale_mass_kg, r.water_dispensed_kg) if x]
    if any(x != n for x in lengths): reasons.add("ARRAY_LENGTH_MISMATCH")
    if r.qc_time_monotonic is False: reasons.add("NONMONOTONE_TIME")
    if r.qc_time_duplicate_stamps: reasons.add("CONFLICTING_REPEATED_TIMESTAMP")
    if any(b <= a for a, b in zip(r.time_s, r.time_s[1:]) if a is not None and b is not None):
        reasons.add("NONMONOTONE_TIME")
    if not r.achieved_pressure_pa: reasons.add("NO_ACHIEVED_PRESSURE_CHANNEL")
    if not r.commanded_pressure_pa: reasons.add("NO_COMMANDED_PRESSURE_CHANNEL")
    if not r.cumulative_scale_mass_kg: reasons.add("NO_CONFIRMED_CUMULATIVE_SCALE_MASS_CHANNEL")
    if not r.scale_flow_kg_s: reasons.add("NO_CONFIRMED_SCALE_FLOW_CHANNEL")
    if r.ambiguous_native_flow_present and not r.scale_flow_kg_s: reasons.add("AMBIGUOUS_NATIVE_FLOW_ONLY")
    if not r.machine: reasons.add("UNKNOWN_PRESSURE_SENSOR_DEVICE_FAMILY")
    if not r.integration_source or not r.integration_source_provenance: reasons.add("UNRESOLVED_INTEGRATION_SOURCE")
    if not r.local_linkage: reasons.add("MISSING_LOCAL_USER_LINKAGE")
    structurally_valid = not reasons.intersection({"UNSUPPORTED_STORE_SCHEMA", "MISSING_TIME", "NONFINITE_TIME", "ARRAY_LENGTH_MISMATCH", "NONMONOTONE_TIME", "CONFLICTING_REPEATED_TIMESTAMP"})
    device_ok = r.machine is not None and r.integration_source is not None and r.integration_source_provenance is not None
    flags = {
        "boundary_summary_eligible": structurally_valid and bool(r.achieved_pressure_pa or r.commanded_pressure_pa),
        "commanded_pressure_profile_eligible": structurally_valid and bool(r.commanded_pressure_pa),
        "achieved_pressure_profile_eligible": structurally_valid and bool(r.achieved_pressure_pa),
        "pressure_tracking_eligible": structurally_valid and bool(r.achieved_pressure_pa and r.commanded_pressure_pa),
        "scale_mass_profile_eligible": structurally_valid and bool(r.cumulative_scale_mass_kg),
        "scale_flow_profile_eligible": structurally_valid and bool(r.scale_flow_kg_s),
        "pressure_flow_context_eligible": structurally_valid and bool(r.achieved_pressure_pa and r.scale_flow_kg_s),
        "ewp_pressure_boundary_executable": structurally_valid and device_ok and bool(r.achieved_pressure_pa or r.commanded_pressure_pa),
        "library_only_eligible": structurally_valid and bool(r.achieved_pressure_pa or r.commanded_pressure_pa),
    }
    if not reasons: reasons.add("OTHERWISE_QUALIFIED")
    return flags, reasons


def counters():
    return Counter(), Counter({name: 0 for name in FLAGS})
