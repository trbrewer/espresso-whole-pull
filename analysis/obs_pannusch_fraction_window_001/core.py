"""Target-independent qualification and frozen identity observer.

Source-derived values are CC-BY-NC-3.0 and are not relicensed as repository code.
"""
from __future__ import annotations
import csv, hashlib, json, math, pathlib, re
from dataclasses import dataclass

TASK = "OBS-PANNUSCH-FRACTION-WINDOW-001"
ASSAY_IDS = (1, 2, 3, 5, 7, 10)
PRIMARY = ("PRED-C01", "PRED-C02", "PRED-C05", "PRED-C06")
EXPECTED = {
    "ExperimentalData_validation.mat": "b5fb0245e5cb67cf3191127f6058624243a38fc0031344f8c93344bb95a84d64",
    "MassData_modelval.mat": "430f922d0df443d9f1b1d629409d9ef4a4967d15535ffa8b5a34f795523faaf3",
    "DesignOfExperiments_Validation_03_22.xlsx": "b7fc864e693ddb40317a4c9493a2fb0c0892b1f1c68f5ce581d48008e21cab57",
    "getExperimentalData_validation.m": "b1a219b851887af69611a9f22c810c7c07f1f3b8e714e6d4ef62500c960deee7",
    "GetMassScale_modelval.m": "9d354ae2fd10148b926e4a5fc9adeafa99ced15d0f24a1a99324a3c81de44b56",
    "ReadMassTimeFromScale.m": "12958952f478afd13387c842e6290ca7551d2511526c6f488a0081a11506192e",
}
RIGHTS = "CC-BY-NC-3.0; source-derived numeric data are not relicensed as repository code"

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def write_json(path, value):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def write_csv(path, fields, rows):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)

def verify_sources(root):
    root = pathlib.Path(root); found = {}
    for name, expected in EXPECTED.items():
        path = root / name
        if not path.is_file(): raise FileNotFoundError(f"required source missing: {name}")
        actual = sha(path)
        if actual != expected: raise ValueError(f"source hash mismatch: {name}: {actual}")
        found[name] = actual
    return found

def source_semantics(text):
    """Require the exact load-bearing mapping without accepting any targets."""
    forbidden = ("cAlcaloids", "TdS", "residual", "RMSE", "predicted_share", "observed_share")
    # Only the pre-chemistry portion of the released script is admissible.
    prefix = text.split("%% TdS", 1)[0]
    if any(x in prefix for x in forbidden): raise ValueError("chemistry reached qualification surface")
    requirements = {
        "mass_load": r"load\('MassData_modelval\.mat'\)",
        "shared_index_flow": r"MassData\(i\*3-3\+j\)\.flow",
        "shared_index_a": r"MassData\(i\*3-3\+j\)\.a",
        "shared_index_b": r"MassData\(i\*3-3\+j\)\.b",
        "cumulative_ten_vials": r"mE\s*=\s*ExperimentalData\(i\)\.run\(j\)\.mE_cum",
        "positive_root": r"\(-b\+sqrt\(b\.\^2-4\.\*a\.\*\(-mE\)\)\)\.\/\(2\.\*a\)",
        "tE_assignment": r"run\(j\)\.tE\s*=\s*tE",
    }
    missing = [key for key, pattern in requirements.items() if not re.search(pattern, prefix)]
    if missing: raise ValueError("source semantics missing: " + ",".join(missing))
    return requirements

def join(records, mapping_proved):
    if len(records) != 24 or not mapping_proved: return []
    return [(i // 3 + 1, i % 3 + 1, i + 1) for i in range(24)]

def unique_matching(candidates):
    """Return a unique perfect matching or fail closed."""
    left = sorted(candidates); solutions = []
    def visit(pos, used, selected):
        if len(solutions) > 1: return
        if pos == len(left): solutions.append(tuple(selected)); return
        key = left[pos]
        for value in sorted(candidates[key]):
            if value not in used: visit(pos + 1, used | {value}, selected + [(key, value)])
    visit(0, set(), [])
    if len(solutions) != 1: raise ValueError("ambiguous or incomplete matching")
    return solutions[0]

def invert_mass(a, b, mass, support):
    if not all(math.isfinite(x) for x in (a, b, mass)) or mass < 0: raise ValueError("invalid mass function")
    lo, hi = support
    if lo < 0 or hi <= lo: raise ValueError("invalid support")
    if min(2*a*lo+b, 2*a*hi+b) <= 0: raise ValueError("non-monotonic mass function")
    disc = b*b + 4*a*mass
    if disc < 0 or a == 0: raise ValueError("no admissible root")
    roots = [(-b+math.sqrt(disc))/(2*a), (-b-math.sqrt(disc))/(2*a)]
    valid = [r for r in roots if lo-1e-12 <= r <= hi+1e-12]
    if len(valid) != 1: raise ValueError("root is not uniquely in support")
    return valid[0]

def cumulative_boundaries(masses):
    if len(masses) < 10 or any((not math.isfinite(x) or x < 0) for x in masses): raise ValueError("invalid vial masses")
    out=[]; total=0.0
    for mass in masses: total += mass; out.append(total)
    return out

def interval_average(fn, start, end):
    if end <= start: raise ValueError("nonpositive interval")
    # Exact for linear histories; deterministic trapezoid is the test oracle here.
    return (fn(start) + fn(end)) / 2

def normalize(concentrations, masses):
    if len(concentrations) != 6 or len(masses) != 6: raise ValueError("six assayed fractions required")
    raw = [max(float(c), 0.0)*float(m) for c,m in zip(concentrations,masses)]
    if not all(math.isfinite(x) for x in raw) or sum(raw) <= 0: raise ValueError("invalid prediction")
    return [x/sum(raw) for x in raw]

def classify(delta, low, high, norm_decreased, conditions_worse, relative):
    if low < 0 < high or (delta == low == high == 0): return "NULL", False
    if high < 0 and norm_decreased and conditions_worse <= 1:
        return "POSITIVE", bool(relative >= .10)
    return "NEGATIVE", False
