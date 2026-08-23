"""Interleaved Stage C R2 solver performance protocol."""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

from .compare import sha256
from .runner import Matrix, explicit, indexed, ROOT


def peak_rss_kib(path: Path) -> int:
    match=re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)",
                    path.read_text())
    if not match:
        raise ValueError(f"peak RSS absent from {path}")
    return int(match.group(1))


def prepare_run(root: Path, name: str, scenario: dict) -> Path:
    case=root/name
    if case.exists():
        raise ValueError(f"refusing reused performance directory: {case}")
    config=root/f"{name}.json"
    config.write_text(json.dumps(scenario,sort_keys=True,indent=2)+"\n")
    subprocess.run([sys.executable,str(ROOT/"scripts/prepare_case.py"),"--root",
        str(ROOT),"--config",str(config),"--nprocs","1","--case-dir",str(case)],
        check=True,stdout=subprocess.DEVNULL)
    subprocess.run(["blockMesh","-case",str(case)],check=True,
        stdout=(case/"blockMesh.log").open("w"),stderr=subprocess.STDOUT)
    return case


def execute(root: Path, label: str, scenario: dict, executable: Path) -> dict:
    case=prepare_run(root,label,scenario)
    timing=case/"time-v.txt"; log=case/"solver.log"
    environment=dict(os.environ,ESPRESSO_CASE_ROOT=str(case))
    start=time.perf_counter_ns()
    with log.open("w") as stream:
        completed=subprocess.run(["/usr/bin/time","-v","-o",str(timing),
            str(executable),"-case",str(case)],env=environment,stdout=stream,
            stderr=subprocess.STDOUT)
    elapsed=(time.perf_counter_ns()-start)/1e9
    if completed.returncode:
        raise RuntimeError(f"performance run failed: {label}")
    return {"label":label,"runtime_s":elapsed,"peak_rss_kib":peak_rss_kib(timing),
            "case_config_sha256":sha256(root/f"{label}.json"),
            "executable_sha256":sha256(executable)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--solver",type=Path,required=True)
    parser.add_argument("--expected-sha256",required=True)
    parser.add_argument("--base-solver",type=Path,required=True)
    parser.add_argument("--expected-base-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(); output=args.output.resolve()
    solver=args.solver.resolve(); base_solver=args.base_solver.resolve()
    if sha256(solver)!=args.expected_sha256 or sha256(base_solver)!=args.expected_base_sha256:
        raise SystemExit("performance executable hash mismatch")
    if output.exists() or ROOT==output or ROOT in output.parents:
        raise SystemExit("performance output must be fresh and external")
    output.mkdir(parents=True)
    factory=Matrix(solver,output)
    common=factory.compact(end=12,dt=.01,axial=128,radial=16)
    modes={
        "base_legacy":(base_solver,common),
        "candidate_legacy":(solver,common),
        "indexed_one":(solver,indexed(common,[explicit("species_a",.28)])),
        "indexed_three":(solver,indexed(common,[explicit("species_a",.07),
            explicit("species_b",.09),explicit("species_c",.12)])),
    }
    records=[]
    for mode,(executable,scenario) in modes.items():
        record=execute(output,f"warmup_{mode}",scenario,executable)
        record.update(kind="warmup",mode=mode,cycle=0,position=0);records.append(record)
    names=list(modes)
    for cycle in range(1,6):
        offset=(cycle-1)%4; order=names[offset:]+names[:offset]
        for position,mode in enumerate(order,1):
            executable,scenario=modes[mode]
            record=execute(output,f"cycle_{cycle}_{position}_{mode}",scenario,executable)
            record.update(kind="measured",mode=mode,cycle=cycle,position=position)
            records.append(record)
    summary={}
    for mode in modes:
        selected=[item for item in records if item["kind"]=="measured" and item["mode"]==mode]
        runtimes=[item["runtime_s"] for item in selected]
        median=statistics.median(runtimes)
        summary[mode]={"minimum_s":min(runtimes),"maximum_s":max(runtimes),
            "median_s":median,"median_absolute_deviation_s":statistics.median(
                abs(value-median) for value in runtimes),
            "maximum_peak_rss_kib":max(item["peak_rss_kib"] for item in selected)}
    overhead=summary["candidate_legacy"]["median_s"]/summary["base_legacy"]["median_s"]
    result={"schema_version":"ewp.sci_md_004.stage_c.r2.performance.v1",
        "status":"PASS" if overhead<=1.10 else "FAIL","records":records,
        "summary":summary,"candidate_legacy_overhead_ratio":overhead,
        "indexed_one_scaling":summary["indexed_one"]["median_s"]/summary["candidate_legacy"]["median_s"],
        "indexed_three_scaling":summary["indexed_three"]["median_s"]/summary["candidate_legacy"]["median_s"],
        "cpu_affinity_policy":sorted(os.sched_getaffinity(0)),
        "machine_load_average":list(os.getloadavg()),
        "timer":"time.perf_counter_ns","rss":"/usr/bin/time -v",
        "case_parameters":{"end_s":12,"delta_t_s":.01,"axial_cells":128,"radial_cells":16}}
    (output/"performance.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True,indent=2))
    if result["status"]!="PASS":
        raise SystemExit(1)


if __name__=="__main__":
    main()
