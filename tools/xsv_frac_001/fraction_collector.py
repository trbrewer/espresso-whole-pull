"""Independent exact-discrete fraction partition oracle (standard library only)."""
from __future__ import annotations

from dataclasses import dataclass
import math

MASS_ABSOLUTE_TOLERANCE_KG = 1e-12
MASS_RELATIVE_TOLERANCE = 1e-10
NUMERICAL_FLOOR_KG = 1e-15
MAX_BOUNDARIES = 10000


@dataclass(frozen=True)
class Species:
    species_id: str
    role: str
    initial_inventory_kg: float


class FractionCollector:
    """Partition rectangular step-flux masses at cumulative mass boundaries."""

    def __init__(self, boundaries_kg, species, emit_terminal_partial=False):
        self.boundaries = tuple(float(x) for x in boundaries_kg)
        if not self.boundaries or len(self.boundaries) > MAX_BOUNDARIES:
            raise ValueError("fraction boundaries must be nonempty and bounded")
        if any(not math.isfinite(x) or x <= 0 for x in self.boundaries):
            raise ValueError("fraction boundaries must be finite and positive")
        if any(b <= a for a, b in zip(self.boundaries, self.boundaries[1:])):
            raise ValueError("fraction boundaries must be strictly increasing")
        if type(emit_terminal_partial) is not bool:
            raise ValueError("emit_terminal_partial must be Boolean")
        self.species = tuple(species)
        self.emit_terminal_partial = emit_terminal_partial
        self.rows = []
        self._next = 0
        self._cumulative = 0.0
        self._water = 0.0
        self._solute = 0.0
        self._species = [0.0] * len(self.species)
        self._start_time = None
        self._last_time = 0.0

    def add_step(self, start_time_s, delta_t_s, water_kg, species_masses_kg,
                 aggregate_solute_kg=None):
        values = [start_time_s, delta_t_s, water_kg, *species_masses_kg]
        if any(not math.isfinite(float(x)) for x in values) or delta_t_s < 0:
            raise ValueError("step values must be finite and delta_t nonnegative")
        if len(species_masses_kg) != len(self.species):
            raise ValueError("species increment count mismatch")
        solute = sum(species_masses_kg) if aggregate_solute_kg is None else float(aggregate_solute_kg)
        if not math.isfinite(solute):
            raise ValueError("aggregate solute increment must be finite")
        scale = max(abs(solute), abs(water_kg + solute))
        if abs(solute - sum(species_masses_kg)) > max(MASS_ABSOLUTE_TOLERANCE_KG, MASS_RELATIVE_TOLERANCE * scale):
            raise ValueError("indexed species increment closure failed")
        components = [float(water_kg), solute, *map(float, species_masses_kg)]
        if any(x < -NUMERICAL_FLOOR_KG for x in components):
            raise ValueError("materially negative collected mass increment")
        components = [0.0 if x < 0 else x for x in components]
        beverage = components[0] + components[1]
        if beverage == 0:
            self._last_time = start_time_s + delta_t_s
            return
        remaining = beverage
        consumed = 0.0
        while remaining > 0 and self._next < len(self.boundaries):
            if self._start_time is None:
                self._start_time = start_time_s + delta_t_s * consumed / beverage
            need = self.boundaries[self._next] - self._cumulative
            share = min(remaining, need) / beverage
            allocation = beverage * share
            self._water += components[0] * share
            self._solute += components[1] * share
            for i, value in enumerate(components[2:]):
                self._species[i] += value * share
            self._cumulative += allocation
            consumed += allocation
            remaining -= allocation
            end_time = start_time_s + delta_t_s * consumed / beverage
            if self._next < len(self.boundaries) and abs(self._cumulative - self.boundaries[self._next]) <= max(MASS_ABSOLUTE_TOLERANCE_KG, MASS_RELATIVE_TOLERANCE*self.boundaries[self._next]):
                self._cumulative = self.boundaries[self._next]
                self._emit("complete", end_time, self.boundaries[self._next])
                self._next += 1
                self._start_time = end_time
        self._last_time = start_time_s + delta_t_s

    def _emit(self, status, end_time, requested_upper):
        lower = 0.0 if not self.rows else self.rows[-1]["realized_upper_cumulative_beverage_mass_kg"]
        beverage = self._water + self._solute
        self.rows.append({"fraction_index": len(self.rows)+1, "status": status,
            "requested_lower_cumulative_beverage_mass_kg": lower,
            "requested_upper_cumulative_beverage_mass_kg": requested_upper,
            "realized_lower_cumulative_beverage_mass_kg": lower,
            "realized_upper_cumulative_beverage_mass_kg": self._cumulative,
            "start_time_s": self._start_time, "end_time_s": end_time,
            "water_mass_kg": self._water, "total_solute_mass_kg": self._solute,
            "beverage_mass_kg": beverage,
            "tds_mass_fraction": self._solute/beverage if beverage else 0.0,
            "cumulative_beverage_mass_kg": self._cumulative,
            "water_plus_solute_closure_residual_kg": beverage-self._water-self._solute,
            "species_sum_closure_residual_kg": self._solute-sum(self._species),
            "species_masses_kg": tuple(self._species)})
        self._water = self._solute = 0.0
        self._species = [0.0] * len(self.species)

    def finish(self):
        if self.emit_terminal_partial and self._next < len(self.boundaries) and self._water + self._solute > 0:
            requested = self.boundaries[self._next] if self._next < len(self.boundaries) else None
            self._emit("partial", self._last_time, requested)
        return list(self.rows)

    @property
    def uncompleted_boundaries(self):
        return list(self.boundaries[self._next:])
