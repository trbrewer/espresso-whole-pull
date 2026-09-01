from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from enum import Enum

from .corpus_adapter import AdaptedRecord

FLAGS = ("boundary_summary_eligible", "commanded_pressure_profile_eligible", "achieved_pressure_profile_eligible",
         "pressure_tracking_eligible", "scale_mass_profile_eligible", "scale_flow_profile_eligible",
         "pressure_flow_context_eligible", "ewp_pressure_boundary_executable", "library_only_eligible")


class TransferState(str, Enum):
    COMMAND_TRANSFER_RESOLVED = "COMMAND_TRANSFER_RESOLVED"
    COMMAND_TRANSFER_UNRESOLVED = "COMMAND_TRANSFER_UNRESOLVED"
    ACHIEVED_TRANSFER_RESOLVED = "ACHIEVED_TRANSFER_RESOLVED"
    ACHIEVED_TRANSFER_UNRESOLVED = "ACHIEVED_TRANSFER_UNRESOLVED"


@dataclass(frozen=True, slots=True)
class PressureTransferAuthority:
    """Explicit authority facts. Source strings never imply these facts."""
    integration_controller_family_resolved: bool = False
    pressure_goal_definition_source_verified: bool = False
    command_units_resolved: bool = False
    command_time_basis_resolved: bool = False
    explicitly_commanded_setpoint: bool = False
    target_ramp_operator_compatible: bool = False
    no_achieved_pressure_claim: bool = False
    integration_family_resolved: bool = False
    device_sensor_family_resolved: bool = False
    pressure_measurement_location_documented: bool = False
    achieved_units_calibration_resolved: bool = False
    bed_top_transfer_limitation_explicit: bool = False
    approximation_rule_passes: bool = False

    @property
    def command_state(self) -> TransferState:
        passed = all((self.integration_controller_family_resolved,
                      self.pressure_goal_definition_source_verified,
                      self.command_units_resolved, self.command_time_basis_resolved,
                      self.explicitly_commanded_setpoint,
                      self.target_ramp_operator_compatible,
                      self.no_achieved_pressure_claim))
        return (TransferState.COMMAND_TRANSFER_RESOLVED if passed
                else TransferState.COMMAND_TRANSFER_UNRESOLVED)

    @property
    def achieved_state(self) -> TransferState:
        passed = all((self.integration_family_resolved,
                      self.device_sensor_family_resolved,
                      self.pressure_measurement_location_documented,
                      self.achieved_units_calibration_resolved,
                      self.bed_top_transfer_limitation_explicit,
                      self.approximation_rule_passes))
        return (TransferState.ACHIEVED_TRANSFER_RESOLVED if passed
                else TransferState.ACHIEVED_TRANSFER_UNRESOLVED)


UNRESOLVED_TRANSFER_AUTHORITY = PressureTransferAuthority()


@dataclass(frozen=True, slots=True)
class StructuralStatuses:
    time_base_valid: bool
    achieved_pressure_series_valid: bool
    commanded_pressure_series_valid: bool
    cumulative_scale_mass_series_valid: bool
    scale_flow_series_valid: bool
    water_dispensed_series_valid: bool
    achieved_commanded_pair_valid: bool
    achieved_pressure_scale_flow_pair_valid: bool


def _finite_series(values: tuple[float | None, ...], n: int) -> bool:
    return bool(values) and len(values) == n and all(
        value is not None and math.isfinite(value) for value in values)


def structural_statuses(r: AdaptedRecord) -> tuple[StructuralStatuses, set[str]]:
    reasons: set[str] = set()
    n = len(r.time_s)
    time_valid = bool(n) and all(x is not None and math.isfinite(x) for x in r.time_s)
    if not n: reasons.add("MISSING_TIME")
    elif not time_valid: reasons.add("NONFINITE_TIME")
    if r.qc_time_monotonic is False or any(
            b <= a for a, b in zip(r.time_s, r.time_s[1:])
            if a is not None and b is not None):
        time_valid = False; reasons.add("NONMONOTONE_TIME")
    if r.qc_time_duplicate_stamps:
        time_valid = False; reasons.add("CONFLICTING_REPEATED_TIMESTAMP")

    channels = (("ACHIEVED_PRESSURE", r.achieved_pressure_pa),
                ("COMMANDED_PRESSURE", r.commanded_pressure_pa),
                ("SCALE_FLOW", r.scale_flow_kg_s),
                ("SCALE_MASS", r.cumulative_scale_mass_kg),
                ("WATER_DISPENSED", r.water_dispensed_kg))
    for label, values in channels:
        if values and len(values) != n:
            reasons.update(("ARRAY_LENGTH_MISMATCH", f"ARRAY_LENGTH_MISMATCH_{label}"))

    achieved = time_valid and _finite_series(r.achieved_pressure_pa, n)
    commanded = time_valid and _finite_series(r.commanded_pressure_pa, n)
    scale_flow = time_valid and _finite_series(r.scale_flow_kg_s, n)
    scale_mass = time_valid and _finite_series(r.cumulative_scale_mass_kg, n)
    water = time_valid and _finite_series(r.water_dispensed_kg, n)

    if r.cumulative_scale_mass_kg and len(r.cumulative_scale_mass_kg) == n:
        finite_mass = [x for x in r.cumulative_scale_mass_kg if x is not None and math.isfinite(x)]
        if any(x < 0 for x in finite_mass):
            scale_mass = False; reasons.add("IMPOSSIBLE_NEGATIVE_CUMULATIVE_MASS")
        if any(b < a for a, b in zip(finite_mass, finite_mass[1:])):
            scale_mass = False; reasons.add("MATERIALLY_DECREASING_CUMULATIVE_MASS")

    return StructuralStatuses(time_valid, achieved, commanded, scale_mass, scale_flow, water,
                              achieved and commanded, achieved and scale_flow), reasons


def qualify(r: AdaptedRecord, authority: PressureTransferAuthority = UNRESOLVED_TRANSFER_AUTHORITY
            ) -> tuple[dict[str, bool], set[str]]:
    reasons: set[str] = set()
    if r.schema_version != 6: reasons.add("UNSUPPORTED_STORE_SCHEMA")
    status, structural_reasons = structural_statuses(r); reasons.update(structural_reasons)
    if not r.achieved_pressure_pa: reasons.add("NO_ACHIEVED_PRESSURE_CHANNEL")
    if not r.commanded_pressure_pa: reasons.add("NO_COMMANDED_PRESSURE_CHANNEL")
    if not r.cumulative_scale_mass_kg: reasons.add("NO_CONFIRMED_CUMULATIVE_SCALE_MASS_CHANNEL")
    if not r.scale_flow_kg_s: reasons.add("NO_CONFIRMED_SCALE_FLOW_CHANNEL")
    if r.ambiguous_native_flow_present and not r.scale_flow_kg_s: reasons.add("AMBIGUOUS_NATIVE_FLOW_ONLY")
    if authority.achieved_state is TransferState.ACHIEVED_TRANSFER_UNRESOLVED:
        reasons.add("UNKNOWN_PRESSURE_SENSOR_DEVICE_FAMILY")
    if authority.command_state is TransferState.COMMAND_TRANSFER_UNRESOLVED:
        reasons.add("UNRESOLVED_INTEGRATION_SOURCE")
    if not r.local_linkage: reasons.add("MISSING_LOCAL_USER_LINKAGE")

    schema_ok = r.schema_version == 6
    achieved = schema_ok and status.achieved_pressure_series_valid
    commanded = schema_ok and status.commanded_pressure_series_valid
    scale_mass = schema_ok and status.cumulative_scale_mass_series_valid
    scale_flow = schema_ok and status.scale_flow_series_valid
    command_executable = commanded and authority.command_state is TransferState.COMMAND_TRANSFER_RESOLVED
    achieved_executable = achieved and authority.achieved_state is TransferState.ACHIEVED_TRANSFER_RESOLVED
    flags = {
        "boundary_summary_eligible": achieved or commanded,
        "commanded_pressure_profile_eligible": commanded,
        "achieved_pressure_profile_eligible": achieved,
        "pressure_tracking_eligible": schema_ok and status.achieved_commanded_pair_valid,
        "scale_mass_profile_eligible": scale_mass,
        "scale_flow_profile_eligible": scale_flow,
        "pressure_flow_context_eligible": schema_ok and status.achieved_pressure_scale_flow_pair_valid,
        "ewp_pressure_boundary_executable": command_executable or achieved_executable,
        "library_only_eligible": achieved or commanded,
    }
    if not reasons: reasons.add("OTHERWISE_QUALIFIED")
    return flags, reasons


def counters():
    return Counter(), Counter({name: 0 for name in FLAGS})
