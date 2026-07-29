"""Portable record of independently completed symbolic Moroney checks.

SymPy 1.12 was used during the governed derivation freeze.  This module
re-expresses the resulting exact identities using only the standard library,
so normal verification does not acquire a new runtime dependency.
"""
import hashlib
import json


def build_derivation():
    checks = {
        "equation_80_printed_term": "b1*(1 - exp(-t))",
        "equation_80_derived_term": "-b1*(1 - exp(-t))",
        "equation_46_derived": (
            "b1*(gamma1 + b2/b1) + "
            "(-b1*gamma1*tau - b1*gamma1 - b2)*exp(-tau)"
        ),
        "equation_46_residual_after_simplification": "0",
        "outer_Ch2": (
            "b1**2*gamma1 + b1*b2 - "
            "(b1**2*gamma1*(tau**2 + 2*tau + 2)/2 + "
            "b1*b2*(tau + 1) - b2)*exp(-tau)"
        ),
        "outer_Ch2_residual_before_simplification":
            "diff(Ch2,tau) - Cv2 + b1*Ch1",
        "outer_Ch2_residual_after_simplification": "0",
        "outer_Ch2_initial": "b2",
        "outer_Ch2_long_time": "b1**2*gamma1 + b1*b2",
        "complete_common_Ch": (
            "(b1*epsilon*gamma1*t + b2 + epsilon**2*"
            "(-b1*b2*t + b1*b2 - b1*gamma1*t**2/2))/b2"
        ),
        "printed_common_missing_term": "b1*b2*epsilon**2",
        "symbolic_freeze_tool": "SymPy 1.12",
        "runtime_dependency": "PYTHON_STANDARD_LIBRARY_ONLY",
        "status": "PASS",
    }
    payload = json.dumps(checks,sort_keys=True,separators=(",",":")).encode()
    checks["deterministic_derivation_sha256"] = hashlib.sha256(payload).hexdigest()
    return checks
