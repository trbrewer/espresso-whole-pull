"""Measurement schemas and mass-balance kernels; not extraction physics."""
from dataclasses import dataclass
import math
from typing import Optional

METHODS = {
    "REFRACTOMETRIC", "GRAVIMETRIC_DRY_DOWN",
    "OVEN_DRYING_RETAINED_LIQUID_CORRECTED",
    "PSEUDOCOMPONENT_MODEL_OUTPUT", "OTHER_EXPLICIT",
}
EY_DEFINITIONS = {"BEVERAGE_TDS_TIMES_BEVERAGE_MASS_OVER_DRY_DOSE",
                  "RETAINED_LIQUID_CORRECTED_MASS_OVER_DRY_DOSE"}


@dataclass(frozen=True)
class TDSMeasurement:
    method_id: str
    instrument_make: str
    instrument_model: str
    reported_basis: str
    uncertainty: float
    source_scope: str
    optical_wavelength_nm: Optional[float] = None
    sample_temperature_K: Optional[float] = None
    temperature_compensation: Optional[str] = None
    zeroing_medium: Optional[str] = None
    calibrant: Optional[str] = None
    calibration_standard: Optional[str] = None
    dilution_basis: Optional[str] = None
    filtration_or_centrifugation: Optional[str] = None
    freeze_thaw_status: Optional[str] = None

    def __post_init__(self):
        if self.method_id not in METHODS or not self.reported_basis or not self.source_scope:
            raise ValueError("complete TDS method identity required")
        if not math.isfinite(self.uncertainty) or self.uncertainty < 0:
            raise ValueError("invalid uncertainty")
        if self.method_id == "REFRACTOMETRIC":
            required = (self.instrument_make, self.instrument_model,
                        self.sample_temperature_K, self.temperature_compensation,
                        self.zeroing_medium, self.calibrant,
                        self.calibration_standard, self.dilution_basis,
                        self.filtration_or_centrifugation,
                        self.optical_wavelength_nm, self.freeze_thaw_status)
            if any(x is None or x == "" for x in required):
                raise ValueError("complete refractometric metadata or explicit UNAVAILABLE required")


@dataclass(frozen=True)
class EYConvention:
    definition_id: str
    tds_method_id: str
    mass_or_volume_basis: str
    density_kg_m3: Optional[float]
    dry_dose_basis: str
    retained_liquid_correction: bool
    volatile_loss_correction: bool
    filtration_status: str
    uncertainty_method: str

    def __post_init__(self):
        if self.definition_id not in EY_DEFINITIONS:
            raise ValueError("invalid EY definition")
        if self.tds_method_id not in METHODS:
            raise ValueError("invalid TDS method")
        if self.mass_or_volume_basis not in {"MASS", "VOLUME"}:
            raise ValueError("invalid mass/volume basis")
        if self.mass_or_volume_basis == "VOLUME" and self.density_kg_m3 is None:
            raise ValueError("density required for volume basis")
        if self.density_kg_m3 is not None and (not math.isfinite(self.density_kg_m3)
                                               or self.density_kg_m3 <= 0):
            raise ValueError("invalid density")


@dataclass(frozen=True)
class RetainedLiquidDryingObservation:
    dry_dose_kg: float
    brew_water_kg: float
    beverage_kg: float
    wet_spent_grounds_kg: float
    dry_spent_grounds_kg: float
    volatile_loss_correction_kg: float
    retained_liquid_tds_mass_fraction: float
    dry_dose_uncertainty_kg: float
    beverage_uncertainty_kg: float = 0.0
    wet_spent_uncertainty_kg: float = 0.0
    dry_spent_uncertainty_kg: float = 0.0
    volatile_loss_uncertainty_kg: float = 0.0
    retained_liquid_tds_uncertainty: float = 0.0
    brew_water_uncertainty_kg: float = 0.0

    def __post_init__(self):
        vals = tuple(self.__dict__.values())
        if not all(math.isfinite(x) for x in vals) or min(vals) < 0:
            raise ValueError("masses, fractions and uncertainty must be finite/nonnegative")
        if self.retained_liquid_tds_mass_fraction > 1:
            raise ValueError("TDS fraction exceeds one")


def drying_kernel(o: RetainedLiquidDryingObservation):
    """Return SI mass-balance quantities and conservative RSS uncertainty."""
    retained = o.wet_spent_grounds_kg - o.dry_spent_grounds_kg
    oven = o.dry_dose_kg - o.dry_spent_grounds_kg + o.volatile_loss_correction_kg
    corrected = oven + retained * o.retained_liquid_tds_mass_fraction
    retained_sigma = math.hypot(o.wet_spent_uncertainty_kg,
                                o.dry_spent_uncertainty_kg)
    oven_sigma = math.sqrt(o.dry_dose_uncertainty_kg**2+
                           o.dry_spent_uncertainty_kg**2+
                           o.volatile_loss_uncertainty_kg**2)
    corrected_sigma = math.sqrt(
        o.dry_dose_uncertainty_kg**2+
        o.volatile_loss_uncertainty_kg**2+
        o.retained_liquid_tds_mass_fraction**2 *
        o.wet_spent_uncertainty_kg**2+
        (1+o.retained_liquid_tds_mass_fraction)**2 *
        o.dry_spent_uncertainty_kg**2+
        retained**2*o.retained_liquid_tds_uncertainty**2)
    water_sigma = math.sqrt(o.brew_water_uncertainty_kg**2+
                            o.beverage_uncertainty_kg**2+
                            o.wet_spent_uncertainty_kg**2+
                            o.dry_spent_uncertainty_kg**2)
    if retained < -2*retained_sigma or oven < -2*oven_sigma or corrected < -2*corrected_sigma:
        raise ValueError("negative physical inventory outside uncertainty")
    return {
        "role": "MEASUREMENT_KERNEL_NOT_EXTRACTION_PHYSICS",
        "units": "kg",
        "retained_liquid_mass": retained,
        "oven_dry_extracted_mass": oven,
        "retained_liquid_corrected_extracted_mass": corrected,
        "uncertainty_kg": corrected_sigma,
        "retained_liquid_uncertainty_kg": retained_sigma,
        "oven_dry_uncertainty_kg": oven_sigma,
        "corrected_extracted_uncertainty_kg": corrected_sigma,
        "water_balance_uncertainty_kg": water_sigma,
        "water_balance_residual_kg": o.brew_water_kg-o.beverage_kg-retained,
        "water_balance_zero_required": False,
        "correction_terms": {
            "volatile_loss_kg": o.volatile_loss_correction_kg,
            "retained_solids_kg": retained * o.retained_liquid_tds_mass_fraction,
        },
    }


def assert_compatible(a: TDSMeasurement, b: TDSMeasurement):
    """Reject silent pooling of unlike measurement methods or bases."""
    identity_a=(a.method_id,a.reported_basis,a.instrument_make,a.instrument_model,
                a.optical_wavelength_nm,a.sample_temperature_K,
                a.temperature_compensation,a.zeroing_medium,a.calibrant,
                a.calibration_standard,a.dilution_basis,
                a.filtration_or_centrifugation,a.freeze_thaw_status)
    identity_b=(b.method_id,b.reported_basis,b.instrument_make,b.instrument_model,
                b.optical_wavelength_nm,b.sample_temperature_K,
                b.temperature_compensation,b.zeroing_medium,b.calibrant,
                b.calibration_standard,b.dilution_basis,
                b.filtration_or_centrifugation,b.freeze_thaw_status)
    if identity_a != identity_b:
        raise ValueError("explicit conversion contract required")
    return True
