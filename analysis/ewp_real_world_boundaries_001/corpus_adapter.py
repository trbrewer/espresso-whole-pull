from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AdaptedRecord:
    audit_id: str | None
    local_linkage: str | None
    schema_version: int | None
    time_s: tuple[float | None, ...]
    achieved_pressure_pa: tuple[float | None, ...]
    commanded_pressure_pa: tuple[float | None, ...]
    scale_flow_kg_s: tuple[float | None, ...]
    cumulative_scale_mass_kg: tuple[float | None, ...]
    water_dispensed_kg: tuple[float | None, ...]
    temperature_mix_k: tuple[float | None, ...]
    dose_kg: float | None
    drink_weight_kg: float | None
    duration_s: float | None
    machine: str | None
    integration_source: str | None
    integration_source_provenance: str | None
    ambiguous_native_flow_present: bool
    qc_time_monotonic: bool | None
    qc_time_duplicate_stamps: int | None


def _series(value: Any) -> tuple[float | None, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(float(x) if isinstance(x, (int, float)) else None for x in value)


def _scalar(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None


def adapt(record: dict[str, Any]) -> AdaptedRecord:
    """Read only the frozen allowlist; unknown/outcome/free-text fields are discarded."""
    hy = record.get("hydraulic") if isinstance(record.get("hydraulic"), dict) else {}
    ctx = record.get("context") if isinstance(record.get("context"), dict) else {}
    qc = record.get("qc") if isinstance(record.get("qc"), dict) else {}
    machine = ctx.get("machine") or record.get("machine")
    return AdaptedRecord(
        audit_id=record.get("id") if isinstance(record.get("id"), str) else None,
        local_linkage=record.get("hashed_user") if isinstance(record.get("hashed_user"), str) else None,
        schema_version=record.get("schema_version") if isinstance(record.get("schema_version"), int) else None,
        time_s=_series(hy.get("time__s")),
        achieved_pressure_pa=_series(hy.get("pressure__Pa")),
        commanded_pressure_pa=_series(hy.get("pressure_goal__Pa")),
        scale_flow_kg_s=_series(hy.get("mass_flow_from_scale__kg_per_s")),
        cumulative_scale_mass_kg=_series(hy.get("weight__kg")),
        water_dispensed_kg=_series(hy.get("water_dispensed__kg")),
        temperature_mix_k=_series(hy.get("temperature_mix__K")),
        dose_kg=_scalar(ctx.get("dose__kg")), drink_weight_kg=_scalar(ctx.get("drink_weight__kg")),
        duration_s=_scalar(ctx.get("duration__s")),
        machine=machine if isinstance(machine, str) and machine.strip() else None,
        integration_source=ctx.get("integration_source") if isinstance(ctx.get("integration_source"), str) and ctx.get("integration_source").strip() else None,
        integration_source_provenance=ctx.get("integration_source_provenance") if isinstance(ctx.get("integration_source_provenance"), str) and ctx.get("integration_source_provenance").strip() and ctx.get("integration_source_provenance") != "unknown" else None,
        ambiguous_native_flow_present=bool(_series(hy.get("flow_reported__native"))),
        qc_time_monotonic=qc.get("time_monotonic") if isinstance(qc.get("time_monotonic"), bool) else None,
        qc_time_duplicate_stamps=qc.get("time_duplicate_stamps") if isinstance(qc.get("time_duplicate_stamps"), int) else None,
    )


def public_safe(record: AdaptedRecord) -> dict:
    """Deliberately no generic record serializer; return only nonidentity scalar flags."""
    return {"schema_version": record.schema_version, "has_achieved_pressure": bool(record.achieved_pressure_pa),
            "has_commanded_pressure": bool(record.commanded_pressure_pa), "has_scale_flow": bool(record.scale_flow_kg_s)}
