#!/usr/bin/env python3
"""Fixed-parameter E1 demonstration; native evidence stays outside the checkout.

SOURCE_SCENARIO_CHANGE_ONLY. Waszkiewicz et al. (2025), Zenodo 18046315,
CC-BY-4.0, through the locked Puckworks aggregates. No fitting is performed.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import sys

import numpy as np

import e1_verification as V


def initial_pressures():
    return sorted(set(V.NOMINAL) | {5. + i/4 for i in range(13)})


def extension_pressures(flows):
    window = [p for p in flows if 5. <= p <= 8.]
    peak = max(window, key=lambda p: flows[p])
    extra = []
    if peak <= 5.25:
        extra += [4. + i/4 for i in range(4)]
    if peak >= 7.75:
        extra += [8.25 + i/4 for i in range(4)]
    return [p for p in extra if p not in flows]


def case_config(parameters, early, pressure, history=None, early_pressure=None):
    cfg = V.scenario(parameters, early, pressure, dt=.0025)
    cfg["scenario_id"] = "E1_CAPABILITY"
    cfg["mode"] = "capability_demonstration"
    cfg["claim_ceiling"] = "capability demonstration, not validation; TARGET_EXPOSED; PHYSICAL_VALIDATION=NOT_ESTABLISHED"
    cfg["hydraulics"]["pressure_ramp_time_s"] = 0.
    if history is not None:
        hydraulic = cfg["hydraulics"]
        del hydraulic["target_inlet_pressure_gauge_Pa"]
        del hydraulic["pressure_ramp_time_s"]
        hydraulic["pressure_boundary_model"] = "prescribedPressureHistory"
        hydraulic["prescribed_pressure_boundary"] = {
            "schedule_type": "piecewiseLinear", "times_s": history[0],
            "pressures_gauge_Pa": [p*1e5 for p in history[1]]}
        cfg["e1_whole_bed_closure"]["earlyPressureBar"] = early_pressure
    return cfg


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def execute(work, name, cfg, exe, pressure, forcing, brew=""):
    complete = work/(name+".result.json")
    if complete.exists():
        result = json.loads(complete.read_text())
        if result["config_sha256"] != hashlib.sha256((json.dumps(cfg,indent=2)+"\n").encode()).hexdigest():
            raise ValueError("Attempted reuse with changed configuration")
        if result["trace_sha256"] != digest(work/name/"postProcessing/wholePull/0/traces.csv"):
            raise ValueError("Completed trace changed")
        if not result["balances_and_bounds_qualified"]:
            raise ValueError("Completed run exceeds existing numerical limits")
        return result
    print("START", name, flush=True)
    rows, wall = V.run_case(work, name, cfg, exe, 32)
    balance = V.balance_bounds(rows, cfg)
    qualified = balance.pop("status") == "PASS"
    end = rows[-1]
    saturation = next((r for r in rows if float(r["min_saturation"]) >= 1.), None)
    if saturation is None:
        raise ValueError("Full saturation not reached: "+name)
    result = dict(run=name, forcing=forcing, brew=brew, nominal_pressure_bar=pressure,
        endpoint_flow_g_s=float(end["outlet_flow_m3_s"])*cfg["liquid"]["density_kg_m3"]*1000.,
        first_drip_s=float(end["first_drip_s"]),
        full_saturation_s=float(end["first_drip_s"]),
        saturation_completed_step_s=float(saturation["time_s"]),
        cumulative_outlet_liquid_mass_g=float(end["cup_water_mass_kg"])*1000.,
        wall_seconds=wall, ranks=32, delta_t_s=.0025,
        early_pressure_bar=cfg["e1_whole_bed_closure"]["earlyPressureBar"],
        balances_and_bounds_qualified=qualified, **balance,
        config_sha256=digest(work/(name+".json")),
        trace_sha256=digest(work/name/"postProcessing/wholePull/0/traces.csv"))
    complete.write_text(json.dumps(result,indent=2)+"\n")
    print("COMPLETE", name, json.dumps(result), flush=True)
    if not qualified:
        raise ValueError("Existing balance/boundedness limits exceeded: "+name)
    return result


def run_constants(args):
    params, early = V.saved_inputs(args.puckworks)
    args.work.mkdir(parents=True, exist_ok=True)
    flows = {}
    for pressure in initial_pressures():
        cfg = case_config(params, early, pressure)
        result = execute(args.work, "constant-"+format(pressure,"g").replace(".","p"),
                         cfg, args.exe, pressure, "constant")
        flows[pressure] = result["endpoint_flow_g_s"]
    extra = extension_pressures(flows)
    print("PREDECLARED_EXTENSION", extra, flush=True)
    for pressure in extra:
        execute(args.work, "constant-"+format(pressure,"g").replace(".","p"),
                case_config(params, early, pressure), args.exe, pressure, "constant")


def source_inputs(puckworks, raw):
    """Fixed source observer/clock, saved B1 coefficients, pressure-only inputs."""
    V.saved_inputs(puckworks)
    sys.path.insert(0, str(puckworks))
    from puckworks.analysis import pressure_peak_stage_a as A
    from puckworks.analysis import pressure_peak_stage_b0 as B
    from puckworks.analysis import pressure_peak_scorecard as S
    brews = A.load_brews(puckworks/"puckworks/data/waszkiewicz2025", V.ROOT)
    source = S.select_stage("B0c", root=puckworks)["B1"][0]
    bank = S.fold_bank("B0c", source)
    course = B.load_course(brews, raw, step=.1)
    use = course.t <= 100.
    early_saved = S.onset_inputs(puckworks)
    onset_saved = {float(r["pressure condition bar"]):float(r["delay mean s"])
        for r in V.records(puckworks/V.ONSET) if r["check"] == "condition onset"
        and r["pressure view"] == "RAW PRIMARY" and float(r["threshold scale"]) == 1.}
    rows = []
    reference_trace_se = []
    for i, name in enumerate(brews.ids):
        original = raw/"measurements_time_dependent"/(name+".txt")
        t0,p0,m0,_ = B.raw_trace(original)
        t, p, observed_flow, _ = B.clean_course(t0,p0,m0)
        if t[-1] < 100.:
            raise ValueError("Insufficient observed support: "+name)
        early = float(np.median(p[t <= 2.]))
        # Reconstruct B0c's existing observation mask, never a model input.
        pre = (t0 >= -2.) & (t0 <= 0.)
        baseline = np.median(m0[pre]) if pre.any() else m0[0]
        onset = B.sustained_onset(t,np.interp(t,t0,m0)-baseline,observed_flow)
        if not np.isfinite(onset):
            raise ValueError("Saved B0c observation-mask onset not reproduced: "+name)
        score_mask = (course.t >= onset+2.) & (course.t <= course.ends[i])
        coef = bank[brews.fold[i]]["free"]
        b1 = float(A.predict("B1", coef, brews.pressure[i:i+1], brews.t)[0])
        b1_full = B.predict_course("B1",coef,course.pressure[i:i+1],course.t)[0][0]
        reference_trace_se.append(float(np.mean((b1_full[score_mask]-course.flow[i,score_mask])**2)))
        b1_trace = b1_full[use]
        rows.append(dict(brew=name, nominal_pressure_bar=float(brews.condition[i]),
            times_s=brews.t.tolist(), pressure_bar=brews.pressure[i].tolist(),
            early_pressure_bar=early, observed_endpoint_g_s=float(brews.target[i]),
            trace_times_s=course.t[use].tolist(), observed_trace_g_s=course.flow[i,use].tolist(),
            trace_mask=score_mask[use].tolist(), observed_onset_for_scoring_only_s=float(onset), b1_endpoint_g_s=b1,
            b1_trace_g_s=b1_trace.tolist(), b1_coefficients=coef, fold=brews.fold[i],
            original_sha256=digest(original)))
    for pressure in V.NOMINAL:
        actual = np.mean([r["early_pressure_bar"] for r in rows if r["nominal_pressure_bar"] == pressure])
        if not np.isclose(actual, early_saved[pressure], atol=1e-12, rtol=0):
            raise ValueError("Pressure-only early input differs from saved B0c: "+str(pressure))
        onset = np.mean([r["observed_onset_for_scoring_only_s"] for r in rows if r["nominal_pressure_bar"] == pressure])
        if not np.isclose(onset,onset_saved[pressure],atol=1e-12,rtol=0):
            raise ValueError("B0c observation mask differs from saved onset aggregate: "+str(pressure))
    reproduced = np.mean([np.sqrt(np.mean([(r["b1_endpoint_g_s"]-r["observed_endpoint_g_s"])**2
        for r in rows if r["nominal_pressure_bar"] == p])) for p in V.NOMINAL])
    if not np.isclose(reproduced, float(source["endpoint RMSE g/s"]), atol=1e-12, rtol=0):
        raise ValueError("Saved B0c B1 endpoint score not reproduced")
    trace_reproduced = np.mean([np.sqrt(np.mean(np.array(reference_trace_se)[g])) for g in brews.groups])
    if not np.isclose(trace_reproduced,float(source["full-trace RMSE g/s"]),atol=1e-12,rtol=0):
        raise ValueError("Saved B0c B1 trace score not reproduced")
    print("B1_REPRODUCED", reproduced, "BREWS",len(rows),flush=True)
    print("B1_TRACE_REPRODUCED",trace_reproduced,flush=True)
    return rows


def run_histories(args):
    params, early = V.saved_inputs(args.puckworks)
    inputs = source_inputs(args.puckworks, args.raw)
    args.work.mkdir(parents=True, exist_ok=True)
    (args.work/"source_inputs.json").write_text(json.dumps(inputs)+"\n")
    for row in inputs:
        pressure = row["nominal_pressure_bar"]
        cfg = case_config(params, early, pressure,
            (row["times_s"], row["pressure_bar"]), row["early_pressure_bar"])
        execute(args.work, "history-"+row["brew"], cfg, args.exe, pressure,
                "measured_history", row["brew"])


def delayed_grid(times, pressure, start):
    """Keep the forcing clock; only the zero-mass/zero-flow start is delayed."""
    times, pressure = np.asarray(times), np.asarray(pressure)
    if start < 0 or start >= times[-1]:
        raise ValueError("Delay must be inside the simulation interval")
    absolute = np.r_[start, times[times > start]]
    return absolute, np.interp(absolute, times, pressure)


def python_e1(parameters, times, pressure, early, start=0., evaluator=None):
    if evaluator is None:
        from puckworks.analysis.pressure_peak_stage_b0 import predict_swelling
        evaluator = predict_swelling
    absolute, forcing = delayed_grid(times, pressure, start)
    d = parameters["onsetCS"]*early**(-parameters["onsetN"])
    flow = evaluator("E1", [parameters[k] for k in ("aGPerSBar","pstarBar","tauS")],
        forcing[None,:], absolute-start, np.array([d]), parameters["mcG"])[0][0]
    values = np.interp(times, absolute, flow)
    values[np.asarray(times) < start] = 0.
    return values


def quadratic_peak(pressures, flows):
    """No extrapolation: three neighboring sweep points must bracket a maximum."""
    p, q = np.asarray(pressures), np.asarray(flows)
    top = int(np.argmax(q))
    if top in (0, len(p)-1):
        return None
    a,b,_ = np.polyfit(p[top-1:top+2],q[top-1:top+2],2)
    vertex = -b/(2*a) if a < 0 else np.nan
    return float(vertex) if p[top-1] <= vertex <= p[top+1] else None


def comparison(bounds):
    # Same decision order and +/-0.25-g/s band as saved Stage A/B0c.
    if bounds[1] < 0: return "BETTER"
    if bounds[0] > 0: return "WORSE"
    if bounds[0] >= -.25 and bounds[1] <= .25: return "TIE"
    return "UNRESOLVED"


def grades(rmse, reference, delta, peak, slope):
    label = comparison(delta)
    accuracy = "MEETS" if label in {"TIE","BETTER"} else (
        "NEAR" if label == "UNRESOLVED" and rmse < reference else "MISSES")
    peak_grade = "MEETS" if peak[0] <= 7 and peak[1] >= 5 else (
        "NEAR" if any(peak[0] <= p <= peak[1] for p in (4,8)) else "MISSES")
    if slope[1] >= 0: slope_grade = "MISSES"
    elif slope[0] <= -.0403 and slope[1] >= -.0880: slope_grade = "MEETS"
    elif slope[0] >= -.176 and slope[1] <= -.020: slope_grade = "NEAR"
    else: slope_grade = "MISSES"
    return label, accuracy, peak_grade, slope_grade


def paired_rmse_draws(squared, groups, count=1000, seed=20261103):
    """Stage B0c's paired conditions-then-whole-brews, mean condition RMSE."""
    rng = random.Random(seed)
    groups = [list(map(int,g)) for g in groups]
    draws = []
    for _ in range(count):
        selected = [rng.choice(groups) for _ in groups]
        loss = np.zeros(len(squared))
        for group in selected:
            picked = [rng.choice(group) for _ in group]
            loss += np.sqrt(np.asarray(squared)[:,picked].mean(axis=1))
        draws.append(loss/len(groups))
    return np.asarray(draws)


def response_draws(values, pressure_end, conditions, count=1000, seed=20261103):
    """Retain every nominal condition; paired resampling of whole brews."""
    rng = np.random.default_rng(seed)
    means, pmeans, draws, pdraws = [],[],[],[]
    for p in V.NOMINAL:
        group = np.flatnonzero(conditions == p)
        picks = rng.choice(group,(count,len(group)),replace=True)
        means.append(values[group].mean()); pmeans.append(pressure_end[group].mean())
        draws.append(values[picks].mean(axis=1)); pdraws.append(pressure_end[picks].mean(axis=1))
    y, x = np.asarray(means), np.asarray(pmeans)
    yb, xb = np.asarray(draws).T, np.asarray(pdraws).T
    high = np.asarray(V.NOMINAL) >= 9
    slope = lambda p,q: float(np.dot(p-p.mean(),q-q.mean())/np.dot(p-p.mean(),p-p.mean()))
    slopes = np.array([slope(p[high],q[high]) for p,q in zip(xb,yb)])
    peaks = np.asarray(V.NOMINAL)[np.argmax(yb,axis=1)]
    return dict(slope=slope(x[high],y[high]), slope_interval=np.quantile(slopes,[.025,.975]).tolist(),
        peak=float(V.NOMINAL[int(np.argmax(y))]),peak_interval=np.quantile(peaks,[.025,.975]).tolist(),
        means=y.tolist(), intervals=np.quantile(yb,[.025,.975],axis=0).T.tolist())


def trace_flow(path, density):
    with Path(path).open() as stream:
        reader=csv.reader(stream); header=next(reader)
        it,iq=header.index("time_s"),header.index("outlet_flow_m3_s")
        values=np.array([(float(r[it]),float(r[iq])*density*1000.) for r in reader])
    return values[:,0],values[:,1]


def score_predictions(inputs, endpoints, traces, pressure_end):
    conditions=np.array([r["nominal_pressure_bar"] for r in inputs])
    target=np.array([r["observed_endpoint_g_s"] for r in inputs])
    baseline=np.array([r["b1_endpoint_g_s"] for r in inputs])
    groups=[np.flatnonzero(conditions==p) for p in V.NOMINAL]
    loss=lambda se: float(np.mean([np.sqrt(se[g].mean()) for g in groups]))
    squared=np.array([(baseline-target)**2,(np.asarray(endpoints)-target)**2])
    draws=paired_rmse_draws(squared,groups)
    delta=np.quantile(draws[:,1]-draws[:,0],[.025,.975]).tolist()
    response=response_draws(np.asarray(endpoints),np.asarray(pressure_end),conditions)
    rmse,base=loss(squared[1]),loss(squared[0])
    label,accuracy,peak,slope=grades(rmse,base,delta,response["peak_interval"],response["slope_interval"])
    trace_squared=[]; b1_trace_squared=[]; full_squared=[]; b1_full_squared=[]
    for r,q in zip(inputs,traces):
        mask=np.array(r["trace_mask"],dtype=bool)
        observed=np.array(r["observed_trace_g_s"])
        trace_squared.append(np.mean((np.asarray(q)[mask]-observed[mask])**2))
        b1_trace_squared.append(np.mean((np.array(r["b1_trace_g_s"])[mask]-observed[mask])**2))
        full = np.asarray(r["trace_times_s"]) >= 5.
        full_squared.append(np.mean((np.asarray(q)[full]-observed[full])**2))
        b1_full_squared.append(np.mean((np.array(r["b1_trace_g_s"])[full]-observed[full])**2))
    td=paired_rmse_draws(np.array([b1_trace_squared,trace_squared]),groups)
    fd=paired_rmse_draws(np.array([b1_full_squared,full_squared]),groups)
    return dict(endpoint_rmse_g_s=rmse, endpoint_rmse_interval_g_s=np.quantile(draws[:,1],[.025,.975]).tolist(),
        b1_endpoint_rmse_g_s=base, endpoint_change_percent=100*(rmse/base-1),
        paired_difference_g_s=rmse-base, paired_interval_g_s=delta, comparison=label,
        accuracy_grade=accuracy, peak_grade=peak, slope_grade=slope,
        trace_rmse_g_s=loss(np.array(trace_squared)),
        trace_rmse_interval_g_s=np.quantile(td[:,1],[.025,.975]).tolist(),
        b1_trace_rmse_g_s=loss(np.array(b1_trace_squared)),
        trace_change_percent=100*(loss(np.array(trace_squared))/loss(np.array(b1_trace_squared))-1),
        startup_inclusive_trace_rmse_g_s=loss(np.array(full_squared)),
        startup_inclusive_trace_interval_g_s=np.quantile(fd[:,1],[.025,.975]).tolist(),
        b1_startup_inclusive_trace_rmse_g_s=loss(np.array(b1_full_squared)), **response)


def output_index(case):
    """Hash every retained native file; publish the index hash, not native data."""
    rows=[dict(path=p.relative_to(case).as_posix(),sha256=digest(p))
          for p in sorted(case.rglob("*")) if p.is_file()]
    path=case.parent/(case.name+".files.sha256.json")
    path.write_text(json.dumps(rows,indent=2)+"\n")
    return dict(native_file_count=len(rows),native_checksum_index_file=path.name,
                native_checksum_index_sha256=digest(path))


def generate_report(args):
    params, early=V.saved_inputs(args.puckworks)
    sys.path.insert(0,str(args.puckworks))
    inputs=json.loads((args.work/"source_inputs.json").read_text())
    records=[json.loads(p.read_text()) for p in sorted(args.work.glob("*.result.json"))]
    constant={r["nominal_pressure_bar"]:r for r in records if r["forcing"]=="constant"}
    histories={r["brew"]:r for r in records if r["forcing"]=="measured_history"}
    expected=set(initial_pressures())|set(extension_pressures({p:constant[p]["endpoint_flow_g_s"] for p in initial_pressures()}))
    if set(constant)!=expected or set(histories)!={r["brew"] for r in inputs} or len(inputs)!=56:
        raise ValueError("Demonstration run set incomplete or differs from declared sweep")
    if not all(r["balances_and_bounds_qualified"] for r in records):
        raise ValueError("A native run exceeds existing balance/boundedness limits")
    args.out.mkdir(parents=True,exist_ok=True)
    density=json.loads((V.ROOT/"config/reference_R0.json").read_text())["liquid"]["density_kg_m3"]
    constant_predictions={}; constant_traces={}; differences=[]
    for p,r in sorted(constant.items()):
        times=np.linspace(0,100,1000); pressure=np.full(1000,p)
        original=python_e1(params,times,pressure,r["early_pressure_bar"])
        delayed=python_e1(params,times,pressure,r["early_pressure_bar"],r["full_saturation_s"])
        constant_predictions[p]=original[-1]
        constant_traces[p]=trace_flow(args.work/r["run"]/"postProcessing/wholePull/0/traces.csv",density)
        r.update(pressure_basis="RAW_LINE_AS_INLET_GAUGE",prescribed_pressure_at_100_bar=p,
            python_original_endpoint_g_s=float(original[-1]),python_delayed_endpoint_g_s=float(delayed[-1]),
            startup_offset_g_s=float(delayed[-1]-original[-1]),
            remainder_g_s=float(r["endpoint_flow_g_s"]-delayed[-1]))
    endpoint=[]; actual_pressure=[]; solver_traces=[]; python_traces=[]; python_endpoints=[]
    for row in inputs:
        r=histories[row["brew"]]
        times=np.asarray(row["times_s"]); pressure=np.asarray(row["pressure_bar"])
        original=python_e1(params,times,pressure,r["early_pressure_bar"])
        delayed=python_e1(params,times,pressure,r["early_pressure_bar"],r["full_saturation_s"])
        native_t,native_q=trace_flow(args.work/r["run"]/"postProcessing/wholePull/0/traces.csv",density)
        solver_traces.append(np.interp(row["trace_times_s"],native_t,native_q))
        python_traces.append(np.interp(row["trace_times_s"],times,original))
        endpoint.append(r["endpoint_flow_g_s"]); actual_pressure.append(pressure[-1]);python_endpoints.append(original[-1])
        r.update(pressure_basis="RAW_LINE_AS_INLET_GAUGE",prescribed_pressure_at_100_bar=float(pressure[-1]),
            python_original_endpoint_g_s=float(original[-1]),python_delayed_endpoint_g_s=float(delayed[-1]),
            startup_offset_g_s=float(delayed[-1]-original[-1]),
            remainder_g_s=float(r["endpoint_flow_g_s"]-delayed[-1]))
    for forcing in ("constant","measured_history"):
        for p in V.NOMINAL:
            group=[r for r in records if r["forcing"]==forcing and r["nominal_pressure_bar"]==p]
            mean=lambda key:float(np.mean([r[key] for r in group]))
            differences.append(dict(forcing=forcing,pressure_bar=p,brews_or_cases=len(group),
                mean_prescribed_pressure_at_100_bar=mean("prescribed_pressure_at_100_bar"),
                python_original_g_s=mean("python_original_endpoint_g_s"),
                python_delayed_g_s=mean("python_delayed_endpoint_g_s"),solver_g_s=mean("endpoint_flow_g_s"),
                startup_offset_g_s=mean("startup_offset_g_s"),remainder_g_s=mean("remainder_g_s"),
                total_difference_g_s=mean("startup_offset_g_s")+mean("remainder_g_s")))
    constant_endpoints=[constant[r["nominal_pressure_bar"]]["endpoint_flow_g_s"] for r in inputs]
    ct=[np.interp(r["trace_times_s"],*constant_traces[r["nominal_pressure_bar"]]) for r in inputs]
    conditions=np.array([r["nominal_pressure_bar"] for r in inputs])
    constant_score=score_predictions(inputs,constant_endpoints,ct,conditions)
    history_score=score_predictions(inputs,endpoint,solver_traces,actual_pressure)
    python_score=score_predictions(inputs,python_endpoints,python_traces,actual_pressure)
    observed=response_draws(np.array([r["observed_endpoint_g_s"] for r in inputs]),np.asarray(actual_pressure),conditions)
    pressure=np.array(sorted(constant)); flow=np.array([constant[p]["endpoint_flow_g_s"] for p in pressure])
    peak=quadratic_peak(pressure,flow)
    for label,score in (("constant",constant_score),("measured_history",history_score),("python_median_measured_history",python_score)):
        score["forcing"]=label
    score_rows=[constant_score,history_score,python_score]
    V.write_csv(args.out/"GRADES.csv",[{k:json.dumps(v) if isinstance(v,list) else v for k,v in s.items()} for s in score_rows])
    V.write_csv(args.out/"PYTHON_SOLVER_DIFFERENCES.csv",differences)
    endpoint_fields=("run","forcing","brew","nominal_pressure_bar","pressure_basis","prescribed_pressure_at_100_bar",
        "endpoint_flow_g_s","first_drip_s", "full_saturation_s",
        "saturation_completed_step_s","cumulative_outlet_liquid_mass_g","early_pressure_bar",
        "python_original_endpoint_g_s","python_delayed_endpoint_g_s","startup_offset_g_s","remainder_g_s",
        "wall_seconds","ranks","delta_t_s","balances_and_bounds_qualified")
    V.write_csv(args.out/"ENDPOINTS.csv",[{k:r[k] for k in endpoint_fields} for r in records])
    manifest=dict(schema="ewp.e1_capability.fixed_prediction_runs.v1",change_class="SOURCE_SCENARIO_CHANGE_ONLY",
        solver_merge_commit="734b15e8c4631c0dda30b6cd67cef00d2eeaed90",puckworks_commit=V.PIN,
        executable_sha256=digest(args.exe),parameters=params,delta_t_s=.0025,ranks=32,scheduling="sequential",
        native_software="OpenFOAM Foundation 12; espressoWholePullFoam",
        unchanged_source_sha256={name:digest(V.ROOT/name) for name in
            ("solver/espressoWholePullFoam/espressoWholePullFoam.C","solver/espressoWholePullFoam/e1EffectivePermeability.H",
             "scripts/prepare_case.py","config/reference_R0.json","dependencies/puckworks.lock.json")},
        hardware="AMD Ryzen Threadripper 3990X; 64 physical cores; 251 GiB RAM; 32 MPI ranks per case",
        numerical_environment=dict(python=sys.version.split()[0],**{name:importlib.metadata.version(name)
            for name in ("numpy","scipy","numba","matplotlib")}),
        bootstrap=dict(resamples=1000,seed=20261103,unit="whole brew, paired, equal condition weight; fixed predictions"),
        pressure_conventions=dict(primary="raw line mapped to inlet gauge pressure",
            constant_early_input="INTERPOLATED_INPUTS: median of saved training-fold pressure interpolants",
            history_early_input="median measured raw pressure over stable-clock 0–2 s; never observed onset",
            slope="nominal pressure for constant forcing; actual endpoint raw pressure for measured histories"),
        trace_observer="B0c 0.1-s observation grid; primary mask observed onset+2 s through 100 s, scoring only; secondary 5–100 s",
        source_datasets=["waszkiewicz2025/traces_per_brew","waszkiewicz2025/equilibrium_windows"],
        data_availability="FILES_INSPECTED: pinned aggregates, saved coefficients and original pressure/mass traces; duplicate alias excluded",
        source_attribution="Waszkiewicz et al. (2025), Zenodo 18046315, CC-BY-4.0",
        target_exposure="RETROSPECTIVE TARGET_EXPOSED; transferred medians combine fits exposed to these brews",
        physical_validation="NOT_ESTABLISHED",constant_pressures_bar=pressure.tolist(),
        continuous_solver_peak_bar=peak,observed_continuous_peak_bar=6.1,observed_continuous_peak_interval_bar=[5.9,6.3],
        native_wall_seconds=sum(r["wall_seconds"] for r in records),
        native_core_hours=sum(r["wall_seconds"]*r["ranks"] for r in records)/3600.,
        inputs_sha256={name:digest(args.puckworks/name) for name in
            (V.CSV,V.ONSET,"puckworks/data/waszkiewicz2025/traces_per_brew.csv","puckworks/data/waszkiewicz2025/equilibrium_windows.csv")},
        originals=[dict(brew=r["brew"],sha256=r["original_sha256"]) for r in inputs],
        runs=[dict(r,**output_index(args.work/r["run"])) for r in records])
    (args.out/"RUN_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    plot_report(args,params,early,constant,observed)
    write_summary(args,constant_score,history_score,python_score,manifest,differences)
    print("REPORT",json.dumps({k:v for k,v in manifest.items() if k in
        {"native_wall_seconds","native_core_hours","continuous_solver_peak_bar"}}),flush=True)


def plot_report(args,parameters,early,constant,observed):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    grid=np.arange(1.,13.0001,.05);times=np.linspace(0,100,1000)
    curve=[python_e1(parameters,times,np.full(1000,p),V.early_input(p,early))[-1] for p in grid]
    fig,ax=plt.subplots(figsize=(7.2,3.2),layout="constrained")
    means=np.asarray(observed["means"]); intervals=np.asarray(observed["intervals"])
    ax.axvspan(5,7,color="#b4cdbb",alpha=.35,label="5–7 bar target band")
    ax.errorbar(V.NOMINAL,means,yerr=np.array([means-intervals[:,0],intervals[:,1]-means]),
        fmt="o",color="#20262b",capsize=3,label="Observed endpoint; 95% whole-brew intervals")
    p=sorted(constant)
    ax.plot(p,[constant[x]["endpoint_flow_g_s"] for x in p],"o-",color="#276997",markersize=3,label="EWP E1 constant-pressure sweep")
    ax.plot(grid,curve,color="#d47c31",linestyle="--",label="Python E1; unchanged transferred medians")
    ax.set(xlabel="Nominal raw / inlet gauge pressure (bar)",ylabel="100-s endpoint flow (g/s)",xlim=(.7,13.3))
    ax.grid(alpha=.18);ax.legend(fontsize=7,loc="lower center",title="Constant curves: INTERPOLATED_INPUTS",title_fontsize=7)
    ax.set_title("capability demonstration, not validation",fontsize=11)
    fig.savefig(args.out/"FIGURE.png",dpi=180);plt.close(fig)


def write_summary(args,constant,history,python,manifest,differences):
    def band(v):return f"[{v[0]:.4f}, {v[1]:.4f}]"
    def row(name,s):
        return (f"| {name} | {s['endpoint_rmse_g_s']:.3f} ({s['endpoint_change_percent']:+.1f}%) / {s['trace_rmse_g_s']:.3f} | "
            f"{s['accuracy_grade']} ({s['comparison']}) | {s['peak']:g} {s['peak_interval']} — {s['peak_grade']} | "
            f"{s['slope']:.4f} {band(s['slope_interval'])} — {s['slope_grade']} |")
    nominal=[r for r in differences if r["forcing"]=="constant"]
    offsets=np.array([r["startup_offset_g_s"] for r in nominal]); remainder=np.array([r["remainder_g_s"] for r in nominal])
    total=np.array([r["total_difference_g_s"] for r in nominal])
    fraction=100*np.sum(np.abs(offsets))/np.sum(np.abs(total))
    peak_region=[dict(pressure_bar=r["nominal_pressure_bar"],startup_offset_g_s=r["startup_offset_g_s"])
        for r in manifest["runs"] if r["forcing"] == "constant" and 4<=r["nominal_pressure_bar"]<=8]
    largest=max(peak_region,key=lambda r:abs(r["startup_offset_g_s"]))
    peak=manifest["continuous_solver_peak_bar"]
    peak_text="unresolved (no bracketed concave maximum)" if peak is None else f"{peak:.3f} bar"
    next_step=("Owner: consider **use the E1 permeability (M=0) during wetting**; the start-up offset exceeds 0.05 g/s in the 4–8 bar region. This is a candidate change only, not implemented here."
        if abs(largest["startup_offset_g_s"])>.05 else
        "Owner: review whether the retained peak-location limitation is acceptable for this capability use before authorizing any further solver work.")
    text=f'''# E1 capability demonstration

**capability demonstration, not validation. PHYSICAL_VALIDATION=NOT_ESTABLISHED.**
SOURCE_SCENARIO_CHANGE_ONLY; retrospective, TARGET_EXPOSED: transferred componentwise medians combine saved fits exposed to these brews. No refitting, parameter/tolerance changes or solver changes.

{len(manifest['constant_pressures_bar'])} constant-pressure cases + 56 individual histories; dry R0 geometry, raw line → inlet gauge pressure, 100-s stable clock, 0.0025 s, 32 ranks, sequential. Flow is ρQ×1000 g/s. Balance/boundedness checks meet existing limits.

| Forcing | Endpoint RMSE (% vs B1) / trace RMSE, g/s | Accuracy | Nominal peak [95%], bar | Slope ≥9 bar [95%], g/s/bar |
|---|---|---|---|---|
{row('Constant',constant)}
{row('Measured histories',history)}
| B0c B1 reference | {history['b1_endpoint_rmse_g_s']:.3f} / {history['b1_trace_rmse_g_s']:.3f} | N/A (reference) | — | — |

Unchanged bands: accuracy ±0.25 g/s; slope wholly negative, overlapping [−0.0880, −0.0403]; peak 5–7 bar, or 4/8 bar NEAR. Paired, condition-balanced whole-brew resampling of fixed predictions: 1,000 draws, seed 20261103. Constant-forcing response intervals have zero width, excluding parameter/model uncertainty. Trace support: observed onset+2 to 100 s, as a scoring mask only; the full 5–100 s score is separate. [Full scores](GRADES.csv).

![Observed endpoint flow, solver sweep, Python E1 and the 5–7 bar band](FIGURE.png)

After accounting for wetting, constant-case CFD and Python differ by at most {np.max(np.abs(remainder)):.5f} g/s (geometry/discretisation remainder). The continuous solver peak is **{peak_text}**, versus observed **6.1 [5.9, 6.3] bar**, using a quadratic through the highest sweep point and its neighbors; this descriptive comparison leaves nominal grades unchanged. Measured histories change endpoint RMSE from {constant['endpoint_rmse_g_s']:.3f} to {history['endpoint_rmse_g_s']:.3f} g/s.

Wetting uses R0 permeability (1.77e-15 m²); E1 starts only at `e1Enabled && saturatedAtStepStart`. First drip equals full saturation in this sharp-front model. Delaying Python with M=0/zero flow until saturation explains {fraction:.1f}% of the summed absolute nominal-pressure difference (offset {offsets.min():+.5f} to {offsets.max():+.5f} g/s); the largest 4–8 bar offset is {largest['startup_offset_g_s']:+.5f} g/s at {largest['pressure_bar']:g} bar. [Every run, saturation and M(100)](ENDPOINTS.csv); [decomposition](PYTHON_SOLVER_DIFFERENCES.csv).

Early-pressure inputs: saved training-fold interpolants for constant cases (**INTERPOLATED_INPUTS**), measured 0–2-s pressure medians for histories. Measured onset is never an input.

**Recommended next step:** {next_step}

Native compute: {manifest['native_wall_seconds']/3600:.3f} h sequential / {manifest['native_core_hours']:.2f} core-hours (preparation/analysis excluded). [Manifest; native evidence retained outside Git](RUN_MANIFEST.json). Waszkiewicz et al. (2025), [Zenodo 18046315](https://doi.org/10.5281/zenodo.18046315), CC-BY-4.0; Puckworks `{V.PIN[:8]}` [B0c folds](https://github.com/trbrewer/puckworks/blob/{V.PIN}/{V.CSV}) / [scorecard](https://github.com/trbrewer/puckworks/blob/{V.PIN}/docs/research/PRESSURE_PEAK_SCORECARD/SUMMARY.md).
'''
    (args.out/"SUMMARY.md").write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["constant", "histories", "inputs", "report"])
    parser.add_argument("--puckworks", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--raw", type=Path)
    parser.add_argument("--out", type=Path, default=V.ROOT/"docs/demonstrations/E1_CAPABILITY")
    args = parser.parse_args()
    if args.work.resolve().is_relative_to(V.ROOT):
        raise ValueError("Native evidence must be outside the checkout")
    if args.mode == "constant":
        run_constants(args)
    elif args.mode == "histories":
        run_histories(args)
    elif args.mode == "report":
        generate_report(args)
    else:
        args.work.mkdir(parents=True, exist_ok=True)
        rows = source_inputs(args.puckworks, args.raw)
        (args.work/"source_inputs.json").write_text(json.dumps(rows)+"\n")


if __name__ == "__main__":
    main()
