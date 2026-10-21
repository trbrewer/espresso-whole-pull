#!/usr/bin/env python3
"""Independent, standard-library observation analysis; no upstream code imported.

One exposed original acquisition, one physical puck. The frozen design is PLAN.md.
All row indices are zero-based original JSON-line indices. No data repair.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import hashlib
import json
import math
import platform
import statistics
import subprocess
from pathlib import Path

TASK = "SCI-MD-WASZ-RESTART-RESPONSE-001"
PUCK = "waszkiewicz2025_fig10_restart_puck_01"
REVISION = "fbc33d3380a9c8cff2467bae70fec7137a6ed46f"
BASE = "adb50c634f0e7959eb1e5a63405ee881cde7be72"
PW = "58075bbbce548e63d94106c96b918c1464221514"
PRODUCTION = "fc61c4670ec7bf801e40bb391aab16048b8da26b"
RAW = "measurements_brew_restarting/brew_restarting.txt"
SCRIPT = "plot_singlepanel_brew_restarting.py"
EXPECTED = {
    RAW: ("7940d6aa008e7cae37bb1bf8ceece44fa07d0bff",
          "e82430cde25574140d2026882a883fba21a0f0ac6d9588b15df22571836f68e9"),
    SCRIPT: ("f93c4c2abb6847d70b21df669bd6940089c226b3",
             "aa35ade18cc8b6946164279d6e2e82337435c3165698be932ff3d0f32b47cd74"),
}
DESIGNS = (("PRIMARY", 2, 2), ("SENSITIVITY_A", 3, 2), ("SENSITIVITY_B", 2, 3))
EXPECTED_SPANS = [(2.464, 77.363), (82.974, 93.913), (99.805, 110.559),
                  (117.760, 128.327), (135.621, 146.094), (152.452, 167.319)]
MAX_GAP_MS = 95  # Inspected acquisition cadence, not sensor accuracy/response.


class Unsupported(ValueError):
    """Requested support is unavailable; never fill, bridge or extrapolate."""


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def authenticate(root):
    revision = git(root, "rev-parse", "HEAD")
    files = {}
    for name, (expected_blob, expected_sha) in EXPECTED.items():
        payload = (root / name).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        sha = hashlib.sha256(payload).hexdigest()
        tree_blob = git(root, "rev-parse", REVISION + ":" + name)
        files[name] = dict(bytes=len(payload), git_blob_id=blob, sha256=sha,
                           pinned_tree_blob_id=tree_blob, expected_git_blob_id=expected_blob,
                           source_root_relative_locator=name,
                           url=f"https://github.com/RadostW/espresso/blob/{REVISION}/{name}",
                           authenticated=blob == tree_blob == expected_blob and sha == expected_sha)
    return dict(revision=revision, expected_revision=REVISION, files=files,
                authenticated=revision == REVISION and all(f["authenticated"] for f in files.values()))


def parse(path):
    """Do not drop a malformed/missing row and accidentally join its neighbors."""
    rows = []
    for i, line in enumerate(path.read_text().splitlines()):
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("not an object")
            rows.append(obj)
        except (ValueError, json.JSONDecodeError):
            rows.append({"parse_error": True, "original_index": i})
    return rows


def pressure_state(row):
    if not finite(row.get("t")) or not finite(row.get("p2")):
        return "UNKNOWN"
    return "ACTIVE" if row["p2"] / 100 > 5.5 else "LOW"


def time_order_ok(rows):
    return all(finite(r.get("t")) for r in rows) and all(
        b["t"] > a["t"] for a, b in zip(rows, rows[1:]))


def sample(row, i):
    return dict(original_index=i, time_ms=row.get("t"),
                time_s=row["t"] / 1000 if finite(row.get("t")) else None,
                pressure_bar=row["p2"] / 100 if finite(row.get("p2")) else None)


def segment(rows):
    """Segmentation depends only on pressure/time, never mass."""
    episodes, start, counts = [], 0, collections.Counter()
    for end in range(1, len(rows) + 1):
        if end < len(rows) and pressure_state(rows[end]) == pressure_state(rows[start]):
            continue
        state = pressure_state(rows[start])
        label = {"ACTIVE": "E", "LOW": "L", "UNKNOWN": "U"}[state] + str(counts[state])
        counts[state] += 1
        first, last = sample(rows[start], start), sample(rows[end-1], end-1)
        ps = [r["p2"] / 100 for r in rows[start:end] if finite(r.get("p2"))]
        episodes.append(dict(episode_id=label, physical_puck_id=PUCK, state=state,
            first_index=start, last_index=end-1, sample_count=end-start,
            start_s=first["time_s"], end_s=last["time_s"],
            duration_s=(last["time_s"]-first["time_s"]) if state != "UNKNOWN" else None,
            pressure_min_bar=min(ps) if ps else None, pressure_max_bar=max(ps) if ps else None,
            entering_bracket=[sample(rows[start-1], start-1), first] if start else None,
            exiting_bracket=[last, sample(rows[end], end)] if end < len(rows) else None,
            boundary_meaning="first/last state samples; brackets are not valve commands"))
        start = end
    return episodes


class Observer:
    def __init__(self, rows, max_gap_ms=MAX_GAP_MS, blocked_edges=()):
        self.rows = rows
        self.max_gap_ms = max_gap_ms
        self.blocked_edges = set(blocked_edges)  # edge i connects original i to i+1
        self.ordered = time_order_ok(rows)
        self.times = [r.get("t") for r in rows]

    def edge(self, i, fields):
        if i in self.blocked_edges:
            raise Unsupported(f"DOCUMENTED_DISCONTINUITY_EDGE_{i}")
        a, b = self.rows[i:i+2]
        if any(not finite(r.get(f)) for r in (a, b) for f in ("t", *fields)):
            raise Unsupported(f"MISSING_OR_NONFINITE_ORIGINAL_RECORD_EDGE_{i}")
        dt = b["t"] - a["t"]
        if dt <= 0:
            raise Unsupported(f"NONINCREASING_CLOCK_EDGE_{i}")
        if dt > self.max_gap_ms:
            raise Unsupported(f"UNSUPPORTED_ACQUISITION_GAP_EDGE_{i}")

    def endpoint(self, t_s, field):
        if not self.ordered:
            raise Unsupported("MISSING_OR_NONINCREASING_ORIGINAL_CLOCK")
        # Seconds are used for lookup, so exact acquired endpoints remain exact.
        ts = [t / 1000 for t in self.times]
        k = bisect.bisect_left(ts, t_s)
        if k < len(ts) and ts[k] == t_s:
            left = right = k
        else:
            left, right = k-1, k
            if left < 0 or right >= len(ts):
                raise Unsupported("ENDPOINT_OUTSIDE_ORIGINAL_SUPPORT")
            self.edge(left, (field,))
        if not finite(self.rows[left].get(field)):
            raise Unsupported(f"MISSING_OR_NONFINITE_{field}_AT_{left}")
        width = ts[right] - ts[left]
        fraction = (t_s - ts[left]) / width if width else 0.0
        v0, v1 = self.rows[left][field], self.rows[right][field]
        factor = 0.01 if field == "p2" else 1.0
        return dict(time_s=t_s, left_index=left, right_index=right,
                    left_time_ms=self.times[left], right_time_ms=self.times[right],
                    left_time_s=ts[left], right_time_s=ts[right],
                    left_value=v0*factor, right_value=v1*factor,
                    bracket_width_s=width, interpolation_fraction=fraction,
                    exact_sample=left == right, value=(v0+(v1-v0)*fraction)*factor,
                    field=field, unit="bar" if field == "p2" else "g")

    def support(self, a, b, field, bounds=None):
        if b <= a:
            raise Unsupported("NONPOSITIVE_INTERVAL")
        ea, eb = self.endpoint(a, field), self.endpoint(b, field)
        if bounds and (ea["left_index"] < bounds[0] or eb["right_index"] > bounds[1]):
            raise Unsupported("ENDPOINT_BRACKET_CROSSES_STATE_TRANSITION")
        for i in range(ea["left_index"], eb["right_index"]):
            self.edge(i, (field,))
        return ea, eb

    def pressure(self, a, b, bounds=None):
        ea, eb = self.support(a, b, "p2", bounds)
        history = [dict(relative_time_s=0.0, time_s=a, pressure_bar=ea["value"],
                        original_index=ea["left_index"] if ea["exact_sample"] else None)]
        original = []
        for i in range(ea["left_index"], eb["right_index"]+1):
            r = self.rows[i]
            original.append(sample(r, i))
            t = r["t"] / 1000
            if a < t < b:
                history.append(dict(relative_time_s=t-a, time_s=t,
                                    pressure_bar=r["p2"]/100, original_index=i))
        history.append(dict(relative_time_s=b-a, time_s=b, pressure_bar=eb["value"],
                            original_index=eb["left_index"] if eb["exact_sample"] else None))
        integral = math.fsum((v["time_s"]-u["time_s"]) *
                    (v["pressure_bar"]+u["pressure_bar"])/2 for u,v in zip(history,history[1:]))
        mean = integral/(b-a)
        p = [v["pressure_bar"] for v in history]
        acquired = sorted(v["pressure_bar"] for v in original if a <= v["time_s"] <= b)
        def quantile(f):
            if not acquired:
                return None
            k = (len(acquired)-1)*f
            lo, hi = math.floor(k), math.ceil(k)
            return acquired[lo] + (acquired[hi]-acquired[lo])*(k-lo)
        change = p[-1]-p[0]
        return dict(time_weighted_mean_bar=mean, min_bar=min(p), max_bar=max(p),
                    sample_q25_bar=quantile(.25), sample_median_bar=quantile(.5),
                    sample_q75_bar=quantile(.75), quantile_weighting="original samples within interval; linear rank interpolation",
                    endpoint_change_bar=change, direction="UP" if change>0 else "DOWN" if change<0 else "FLAT",
                    total_variation_bar=math.fsum(abs(v-u) for u,v in zip(p,p[1:])),
                    max_excursion_from_mean_bar=max(abs(v-mean) for v in p),
                    convention="piecewise linear on adjacent original acquisitions; exact trapezoid integral",
                    start=ea, end=eb, original_support=original, history=history)

    def interval(self, identity, episode, kind, a, b, design, guard=None):
        result = dict(interval_id=identity, physical_puck_id=PUCK,
                      episode_id=episode["episode_id"], kind=kind, design=design,
                      start_s=a, end_s=b, duration_s=b-a, guard_s=guard,
                      supported=False, unavailable_reason=None, rate_g_s=None,
                      mass_change_g=None, mass_start=None, mass_end=None, pressure=None)
        try:
            bounds = (episode["first_index"], episode["last_index"])
            ma, mb = self.support(a, b, "m", bounds)
            pressure = self.pressure(a, b, bounds)
            result.update(supported=True, rate_g_s=(mb["value"]-ma["value"])/(b-a),
                          mass_change_g=mb["value"]-ma["value"], mass_start=ma,
                          mass_end=mb, pressure=pressure)
        except Unsupported as error:
            result["unavailable_reason"] = str(error)
        return result


def windows(observer, episodes):
    intervals, eligibility = [], []
    active = [e for e in episodes if e["state"] == "ACTIVE"]
    for design, duration, guard in DESIGNS:
        for j, ep in enumerate(active):
            s, e, ident = ep["start_s"], ep["end_s"], ep["episode_id"]
            if j == 0:
                for k in range(3):
                    b = e-guard-(2-k)*duration
                    kind = "later" if k == 2 else f"drift_{k+1}"
                    intervals.append(observer.interval(f"{design}_{ident}_{kind}", ep, kind,
                                                       b-duration, b, design, guard))
            else:
                early = observer.interval(f"{design}_{ident}_early", ep, "early",
                                           s+guard, s+guard+duration, design, guard)
                later = observer.interval(f"{design}_{ident}_later", ep, "later",
                                           e-guard-duration, e-guard, design, guard)
                nonoverlap = early["end_s"] <= later["start_s"]
                intervals.extend((early, later))
                eligibility.append(dict(design=design, episode_id=ident, physical_puck_id=PUCK,
                    nonoverlap=nonoverlap, separation_between_windows_s=later["start_s"]-early["end_s"],
                    eligible=early["supported"] and later["supported"] and nonoverlap,
                    unavailable_reason=("EARLY_LATER_OVERLAP" if not nonoverlap else
                        early["unavailable_reason"] or later["unavailable_reason"])))
    for ep in episodes:
        if ep["state"] == "LOW":
            intervals.append(observer.interval("OFF_"+ep["episode_id"], ep, "pressure_off_context",
                                                ep["start_s"], ep["end_s"], "CONTEXT"))
    return intervals, eligibility


def value_at(history, t):
    ts = [v["relative_time_s"] for v in history]
    k = bisect.bisect_left(ts, t)
    if k < len(ts) and ts[k] == t:
        return history[k]["pressure_bar"]
    if k == 0 or k == len(ts):
        raise Unsupported("PRESSURE_GRID_EXTRAPOLATION")
    f = (t-ts[k-1])/(ts[k]-ts[k-1])
    return history[k-1]["pressure_bar"]*(1-f)+history[k]["pressure_bar"]*f


def pressure_difference(left, right):
    if not math.isclose(left["duration_s"], right["duration_s"], rel_tol=0, abs_tol=1e-12):
        raise Unsupported("UNEQUAL_PRESSURE_INTERVAL_DURATIONS")
    lh, rh = left["pressure"]["history"], right["pressure"]["history"]
    grid = sorted({v["relative_time_s"] for h in (lh, rh) for v in h})
    # Fixed windows have exact integer durations; no rounding or time warping.
    values = [dict(relative_time_s=t, left_bar=value_at(lh,t), right_bar=value_at(rh,t)) for t in grid]
    d = [v["left_bar"]-v["right_bar"] for v in values]
    integral = math.fsum((grid[i+1]-grid[i])*(d[i]**2+d[i]*d[i+1]+d[i+1]**2)/3
                         for i in range(len(grid)-1))
    return dict(mean_difference_bar=left["pressure"]["time_weighted_mean_bar"]-
                right["pressure"]["time_weighted_mean_bar"],
                rms_mismatch_bar=math.sqrt(integral/left["duration_s"]),
                max_absolute_mismatch_bar=max(map(abs,d)),
                union_knots=values, method="exact integral of squared linear difference on union of relative knots",
                equivalence="NOT_ESTABLISHED_NO_INDEPENDENT_PRESSURE_RESPONSE_BOUND")


def contrast(kind, left, right, eligible=True, reason=None):
    available = left["supported"] and right["supported"] and eligible
    out = dict(contrast_id=left["design"]+"_"+left["episode_id"]+"_"+kind,
        design=left["design"], episode_id=left["episode_id"], physical_puck_id=PUCK,
        kind=kind, left_interval_id=left["interval_id"], right_interval_id=right["interval_id"],
        left_rate_g_s=left["rate_g_s"], right_rate_g_s=right["rate_g_s"],
        left_start_s=left["start_s"], left_end_s=left["end_s"],
        right_start_s=right["start_s"], right_end_s=right["end_s"],
        duration_s=left["duration_s"],
        midpoint_separation_s=(left["start_s"]+left["end_s"]-right["start_s"]-right["end_s"])/2,
        supported=available, unavailable_reason=None if available else
        reason or left["unavailable_reason"] or right["unavailable_reason"],
        difference_g_s=left["rate_g_s"]-right["rate_g_s"] if available else None,
        duplicates_kind="A" if kind=="B" and left["episode_id"]=="E1" else None,
        pressure=pressure_difference(left,right) if available else None)
    return out


def contrasts(intervals, eligibility):
    out = []
    indexed = {(v["design"],v["episode_id"],v["kind"]):v for v in intervals}
    for elig in eligibility:
        design, ep = elig["design"], elig["episode_id"]
        early, later = indexed[(design,ep,"early")], indexed[(design,ep,"later")]
        base = indexed[(design,"E0","later")]
        previous = indexed[(design,"E"+str(int(ep[1:])-1),"later")]
        for kind,left,right in [("A",later,base),("B",later,previous),("C",later,early),("D",early,base)]:
            # All A-D form the declared eligible paired family, without rescue windows.
            out.append(contrast(kind,left,right,elig["eligible"],elig["unavailable_reason"]))
    for design,_,_ in DESIGNS:
        first,second,third = [indexed[(design,"E0",k)] for k in ("drift_1","drift_2","later")]
        out.extend((contrast("DRIFT_2_MINUS_1",second,first),contrast("DRIFT_3_MINUS_2",third,second)))
    return out


def lineage(rows):
    means, derivative, direct = [], [], []
    for i, row in enumerate(rows):
        window = rows[max(0,i-4):i+1]
        means.append(math.fsum(r["m"] for r in window)/5
                     if len(window)==5 and all(finite(r.get("m")) for r in window) else None)
        valid = (i>=5 and means[i] is not None and means[i-1] is not None and
                 finite(row.get("t")) and finite(rows[i-1].get("t")) and row["t"]>rows[i-1]["t"])
        dt = (row["t"]-rows[i-1]["t"])/1000 if valid else None
        derivative.append((means[i]-means[i-1])/dt if valid else None)
        direct.append((row["m"]-rows[i-5]["m"])/(5*dt) if valid else None)
    errors = [abs(a-b) for a,b in zip(derivative,direct) if a is not None]
    return means,derivative,dict(startup_mean_null_indices=[i for i,x in enumerate(means) if x is None],
        startup_derivative_null_indices=[i for i,x in enumerate(derivative) if x is None],
        independent_formula="(m[i]-m[i-5])/(5*((t[i]-t[i-1])/1000)); complete rows only",
        max_formula_difference_g_s=max(errors) if errors else None,
        calculation="trailing five-sample mass mean; adjacent difference/current adjacent elapsed time",
        role="LINEAGE_ONLY_NOT_PRIMARY_DELIVERY_EVIDENCE")


def audit(rows):
    bad = {f:[i for i,r in enumerate(rows) if not finite(r.get(f))] for f in ("t","p2","m")}
    steps = [dict(left_index=i, right_index=i+1, left_time_s=a["t"]/1000,
                  right_time_s=b["t"]/1000, mass_step_g=b["m"]-a["m"])
             for i,(a,b) in enumerate(zip(rows,rows[1:]))
             if all(finite(r.get(f)) for r in (a,b) for f in ("t","m"))]
    dt = [b["t"]-a["t"] for a,b in zip(rows,rows[1:]) if finite(a.get("t")) and finite(b.get("t"))]
    return dict(record_count=len(rows), fields=dict(collections.Counter(k for r in rows for k in r)),
                missing_or_nonfinite=bad,
                all_field_missing_or_nonfinite={f:[i for i,r in enumerate(rows) if not finite(r.get(f))]
                    for f in sorted({k for r in rows for k in r})}, original_time_range_s=[rows[0]["t"]/1000, rows[-1]["t"]/1000],
                sampling_interval_ms_counts=dict(collections.Counter(dt)),
                nonincreasing_edges=[i for i,(a,b) in enumerate(zip(rows,rows[1:]))
                                     if finite(a.get("t")) and finite(b.get("t")) and b["t"]<=a["t"]],
                gaps_over_inspected_cadence=[i for i,d in enumerate(dt) if d>MAX_GAP_MS],
                negative_mass_steps=[s for s in steps if s["mass_step_g"]<0],
                zero_mass_step_count=sum(s["mass_step_g"]==0 for s in steps),
                positive_mass_step_count=sum(s["mass_step_g"]>0 for s in steps),
                mass_step_min=min(steps,key=lambda s:s["mass_step_g"]),
                mass_step_max=max(steps,key=lambda s:s["mass_step_g"]),
                documented_discontinuity_edges=[],
                scale_handling="UNRESOLVED; no same-record handling log or response/calibration bound; no reset repair",
                physical_uncertainty="UNCALIBRATED; decimal precision is not sensor accuracy")


def csv_write(path, records):
    fields = sorted({k for r in records for k in r})
    with path.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n")
        writer.writeheader()
        for record in records:
            writer.writerow({k:json.dumps(v,sort_keys=True,allow_nan=False,separators=(",",":"))
                             if isinstance(v,(dict,list)) else v for k,v in record.items()})


def figure(path, rows, episodes, intervals, derivative):
    """Standalone raw-clock SVG. No plotting dependency or smoothing of raw panels."""
    width,height=1080,720
    left,right=85,1035
    def x(t): return left+(right-left)*t/172
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<g font-family="sans-serif" font-size="13" fill="#172b3a">',
           '<text x="85" y="25" font-size="19">Original Figure 10 recording · one puck · continuous acquisition clock</text>',
           '<text x="85" y="48">Primary: 2 s windows, 2 s guards · blue = early · orange = later · gray = initial drift</text>']
    panels=[(70,185,0,10,"Recorded line pressure (bar)",[r['p2']/100 for r in rows],"#27688a"),
            (285,185,min(r['m'] for r in rows)-5,max(r['m'] for r in rows)+5,"Recorded cup mass (g)",[r['m'] for r in rows],"#222222"),
            (500,150,min(v for v in derivative if v is not None)-.2,max(v for v in derivative if v is not None)+.2,
             "Published five-sample derivative (g/s) · lineage only",derivative,"#7751a8")]
    for top,h,lo,hi,title,values,color in panels:
        def y(v):return top+h-(v-lo)*h/(hi-lo)
        parts.append(f'<text x="85" y="{top-8}">{title}</text>')
        for ep in episodes:
            if ep['state']=='LOW':
                parts.append(f'<rect x="{x(ep["start_s"]):.3f}" y="{top}" width="{x(ep["end_s"])-x(ep["start_s"]):.3f}" height="{h}" fill="#eef1f3"/>')
            if ep['state']=='ACTIVE':
                for t in (ep['start_s'],ep['end_s']):
                    parts.append(f'<path d="M{x(t):.3f},{top}v{h}" stroke="#a2adb4" stroke-dasharray="3 3"/>')
                if top==70:parts.append(f'<text x="{x((ep["start_s"]+ep["end_s"])/2):.3f}" y="{top+15}" text-anchor="middle">{ep["episode_id"]}</text>')
        for it in intervals:
            if it['design']=='PRIMARY':
                fill='#76b6e4' if it['kind']=='early' else '#efb45f' if it['kind']=='later' else '#adb5bd'
                parts.append(f'<rect x="{x(it["start_s"]):.3f}" y="{top}" width="{x(it["end_s"])-x(it["start_s"]):.3f}" height="{h}" fill="{fill}" opacity=".42"/>')
        for k in range(5):
            v=lo+(hi-lo)*k/4
            parts.append(f'<text x="75" y="{y(v)+4:.3f}" text-anchor="end">{v:.1f}</text>')
        points=' '.join(f'{x(r["t"]/1000):.3f},{y(v):.3f}' for r,v in zip(rows,values) if v is not None)
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="1.1"/>')
        parts.append(f'<path d="M{left},{top}v{h}H{right}" fill="none" stroke="#34495e"/>')
    for t in range(0,171,10):parts.append(f'<text x="{x(t):.3f}" y="674" text-anchor="middle">{t}</text>')
    parts.append('<text x="500" y="698">Original acquisition time (s)</text></g></svg>\n')
    path.write_text('\n'.join(parts))


def run(source_root, output):
    output.mkdir(parents=True,exist_ok=True)
    source=authenticate(source_root)
    manifest=dict(task_id=TASK, ewp_base=BASE, puckworks_research_main=PW,
        production_puckworks_lock=PRODUCTION, original_source=source,
        physical_puck_id=PUCK, repository="https://github.com/RadostW/espresso",
        paper="https://arxiv.org/html/2512.21528v1", deposit="https://zenodo.org/records/18046315",
        retrieval_method="reuse verified existing v1.0.1 Git clone; exact HEAD/tree blobs and independent SHA-256",
        reproducible_retrieval=["git init SOURCE_ROOT", "git -C SOURCE_ROOT remote add origin https://github.com/RadostW/espresso.git",
            "git -C SOURCE_ROOT fetch --depth 1 origin "+REVISION, "git -C SOURCE_ROOT checkout --detach FETCH_HEAD"],
        attribution="Waszkiewicz, Myck, Białas, Puciata-Mroczynska, Dzikowski, Szymczak and Lisicki (2025)",
        rights=dict(data="CC-BY-4.0 deposit data per accepted Puckworks provenance and Zenodo metadata",
                    software="GPLv3; inspected only; independently implemented mathematics; no upstream execution/copying"),
        fields=dict(t="milliseconds; analysis time=t/1000 seconds; original clock",
                    p2="recorded pressure; line pressure=p2/100 bar",m="recorded cup mass in grams",
                    other="U, v1, v2, p1 uninterpreted; p1 not asserted independent puck pressure"),
        runtime=dict(python=platform.python_version(), dependencies="Python standard library only"),
        plan_sha256=sha256(Path(__file__).resolve().parents[2]/'docs/analysis/sci_md_wasz_restart_response_001/PLAN.md'),
        implementation_sha256=sha256(Path(__file__)),
        raw_payloads="outside repository; locators relative to explicit --source-root",
        evidence_root_convention="external task evidence directory; full logs referenced by relative locator in CHECKS.json")
    dump(output/'SOURCE_MANIFEST.json',manifest)
    if not source['authenticated']:
        dump(output/'RESULT.json',dict(task_id=TASK,status="SOURCE_AUTHENTICATION_FAILED",source=source))
        raise Unsupported("SOURCE_AUTHENTICATION_FAILED; diagnostic retained; no substitute trace")
    rows=parse(source_root/RAW)
    episodes=segment(rows)
    observed=[(e['start_s'],e['end_s']) for e in episodes if e['state']=='ACTIVE']
    if observed!=EXPECTED_SPANS:
        dump(output/'RESULT.json',dict(task_id=TASK,status="PRESSURE_SUPPORT_MISMATCH",observed=observed,expected=EXPECTED_SPANS))
        raise Unsupported("PRESSURE_SUPPORT_MISMATCH; diagnose rather than force expected boundaries")
    observer=Observer(rows)
    intervals,eligibility=windows(observer,episodes)
    comparisons=contrasts(intervals,eligibility)
    _,derivative,lineage_check=lineage(rows)
    common=sorted(set.intersection(*[{e['episode_id'] for e in eligibility if e['design']==d and e['eligible']}
                                   for d,_,_ in DESIGNS]))
    result=dict(task_id=TASK, status="COMPLETED_DESCRIPTIVE_OBSERVATION",
        declaration="G1 / NO_GOVERNING_PHYSICS_CHANGE", evidence_class=["RESEARCH_ONLY","RETROSPECTIVE","SOURCE_INTERNAL","TARGET_EXPOSED"],
        physical_validation="NOT_ESTABLISHED", physical_puck_id=PUCK, physical_puck_count=1,
        accepted_between_brew_cohort_modified=False, physical_uncertainty="UNCALIBRATED",
        acquisition_audit=audit(rows), episodes=episodes, designs=[dict(name=n,duration_s=d,guard_s=g) for n,d,g in DESIGNS],
        eligibility=eligibility, common_supported_restart_subset=common, intervals=intervals, contrasts=comparisons,
        published_observer_lineage=lineage_check,
        conditional_hypothesis="q(t)=F(P_line(t)); time-invariant memoryless F, stable apparatus, other relevant conditions and observation response",
        pressure_only_exclusion="UNRESOLVED_WITHOUT_INDEPENDENT_PRESSURE_RESPONSE_AND_OBSERVATION_BOUNDS",
        causal_attribution="NOT_ESTABLISHED; no uninterrupted control or same-record chemistry/temperature/structure/response qualification",
        development_consequence="Retain quantitative within-puck later delivery observations; withhold interruption-specific mechanical requirement; no automatic successor")
    for name,records in [('EPISODES.csv',episodes),('INTERVALS.csv',intervals),('CONTRASTS.csv',comparisons)]:
        csv_write(output/name,records)
    dump(output/'RESULT.json',result)
    figure(output/'RAW_CLOCK.svg',rows,episodes,intervals,derivative)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.source_root,args.output)
    print(json.dumps(dict(status=result['status'],common_supported_restarts=result['common_supported_restart_subset'],
                         intervals=len(result['intervals']),contrasts=len(result['contrasts'])),allow_nan=False))


if __name__=='__main__':
    main()
