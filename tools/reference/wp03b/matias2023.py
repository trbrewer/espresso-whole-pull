"""Matias 2023 quasi-steady one-dimensional outlet references."""
import math


def _valid(pe, sh, xi, length):
    if not all(math.isfinite(x) for x in (pe, sh, xi, length)):
        raise ValueError("dimensionless groups must be finite")
    if pe < 0 or sh < 0 or xi < 0 or length <= 0:
        raise ValueError("invalid Matias domain")


def low_pe(cs, sh, xi, length=1.0):
    """Low-Pe outlet concentration, in the same concentration units as cs."""
    _valid(0.0, sh, xi, length)
    if not math.isfinite(cs) or cs < 0:
        raise ValueError("cs must be finite and nonnegative")
    return cs * (1.0 - 1.0 / math.cosh(length * math.sqrt(sh * xi)))


def high_pe(cs, pe, sh, xi, length=1.0):
    """High-Pe outlet concentration, in the same concentration units as cs."""
    _valid(pe, sh, xi, length)
    if pe <= 0 or not math.isfinite(cs) or cs < 0:
        raise ValueError("positive Pe and finite nonnegative cs required")
    return -cs * math.expm1(-length * sh * xi / pe)


def full_outlet(cs, pe, sh, xi, length=1.0):
    """Full Delta/S-plus/S-minus closed-form outlet solution."""
    _valid(pe, sh, xi, length)
    if not math.isfinite(cs) or cs < 0:
        raise ValueError("cs must be finite and nonnegative")
    if sh == 0 or xi == 0:
        return 0.0
    delta = math.hypot(pe, 2.0 * math.sqrt(sh * xi))
    sp, sm = (pe + delta) / 2.0, (pe - delta) / 2.0
    em = math.exp(sm * length)
    ratio = math.exp(-delta * length)
    a_at_outlet = cs * sm * em / (sp - sm * ratio)
    a = 0.0 if sp * length > 700 else a_at_outlet * math.exp(-sp * length)
    b = -cs - a
    value = cs + a_at_outlet + b * em
    if not math.isfinite(value):
        raise ArithmeticError("nonfinite closed-form result")
    return value


def front_gating_error(sh_over_pe):
    """Parameter-free declared linear small-ratio gating-error trend."""
    if not math.isfinite(sh_over_pe) or sh_over_pe < 0:
        raise ValueError("Sh/Pe must be finite and nonnegative")
    return sh_over_pe / (1.0 + sh_over_pe)
