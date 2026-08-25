"""Generic H0 composition closure; this module contains no transport physics."""
from __future__ import annotations

import math


def _interp(history: list[dict], mass_kg: float) -> float:
    if mass_kg < history[0]["beverage_mass_kg"] or mass_kg > history[-1]["beverage_mass_kg"]:
        raise ValueError("beverage mass is outside aggregate history")
    for left, right in zip(history, history[1:]):
        if left["beverage_mass_kg"] <= mass_kg <= right["beverage_mass_kg"]:
            span = right["beverage_mass_kg"] - left["beverage_mass_kg"]
            weight = 0.0 if span == 0 else (mass_kg-left["beverage_mass_kg"])/span
            return left["cup_solute_mass_kg"] + weight*(right["cup_solute_mass_kg"]-left["cup_solute_mass_kg"])
    return history[-1]["cup_solute_mass_kg"]


def compose(*, aggregate_history: list[dict], inventories: dict[str, float],
            dry_dose_kg: float, fractions: list[dict], aggregate_inventory_fraction: float,
            uncertainty: dict | None = None) -> dict:
    """Apply aggregate extracted fraction to arbitrary indexed inventories.

    Inventories and ``aggregate_inventory_fraction`` are dry-basis mass fractions.
    Fraction bounds use beverage mass in kg. Concentration is kg/kg beverage.
    """
    if dry_dose_kg <= 0 or aggregate_inventory_fraction <= 0 or not aggregate_history:
        raise ValueError("positive dose, aggregate inventory, and history are required")
    if any(not name or value < 0 or not math.isfinite(value) for name, value in inventories.items()):
        raise ValueError("species names and inventories must be finite and nonnegative")
    aggregate_initial = dry_dose_kg*aggregate_inventory_fraction
    rows = []
    for fraction in fractions:
        lo, hi = fraction["lower_beverage_mass_kg"], fraction["upper_beverage_mass_kg"]
        if hi <= lo:
            raise ValueError("fraction upper bound must exceed lower bound")
        aggregate_lo, aggregate_hi = _interp(aggregate_history, lo), _interp(aggregate_history, hi)
        extracted_fraction_lo, extracted_fraction_hi = aggregate_lo/aggregate_initial, aggregate_hi/aggregate_initial
        for name, inventory_fraction in sorted(inventories.items()):
            initial = dry_dose_kg*inventory_fraction
            cup_lo, cup_hi = initial*extracted_fraction_lo, initial*extracted_fraction_hi
            mass = cup_hi-cup_lo
            rows.append({"fraction_id": fraction["fraction_id"], "species_id": name,
                         "species_cup_mass_kg": mass,
                         "species_concentration_kg_per_kg_beverage": mass/(hi-lo),
                         "species_extraction_fraction": cup_hi/initial if initial else 0.0,
                         "aggregate_total_solids_cup_mass_kg": aggregate_hi-aggregate_lo})
    final_fraction = aggregate_history[-1]["cup_solute_mass_kg"]/aggregate_initial
    return {"species": rows, "aggregate_total_solids_consistency_kg": 0.0,
            "inventory_closure": {name: {"initial_kg": dry_dose_kg*value,
                "cup_kg": dry_dose_kg*value*final_fraction,
                "remaining_kg": dry_dose_kg*value*(1-final_fraction)}
                for name, value in sorted(inventories.items())},
            "uncertainty_components": uncertainty or {}}
