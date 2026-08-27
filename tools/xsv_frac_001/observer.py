"""Independent trace-differenced discrete-stream fraction observer."""
from __future__ import annotations
import csv, json, math
from pathlib import Path
from .fraction_collector import FractionCollector, Species

MASS_ABS=1e-12; MASS_REL=1e-10; TIME_ABS=1e-12; TIME_REL=1e-10; RATIO_ABS=1e-10

def rows(path):
    with Path(path).open(newline="",encoding="utf-8") as stream: return list(csv.DictReader(stream))
def close_mass(a,b): return abs(a-b)<=max(MASS_ABS,MASS_REL*abs(b))
def close_time(a,b,dt): return abs(a-b)<=max(TIME_ABS,TIME_REL*max(abs(b),abs(dt)))

def configured_species(scenario):
    extraction=scenario["extraction"]
    if extraction.get("model")!="indexed_passive_species_first_order_with_capacity_ceiling":
        return [Species("legacy_effective_solute","legacyEffectiveSolute",scenario["coffee_bed"]["dry_dose_kg"]*scenario["coffee_bed"]["initial_extractable_fraction_dry_basis"])]
    result=[]; explicit=0.0; total=scenario["coffee_bed"]["dry_dose_kg"]*scenario["coffee_bed"]["initial_extractable_fraction_dry_basis"]
    for raw in extraction["species"]:
        if raw["role"]=="explicit_inventory":
            mass=scenario["coffee_bed"]["dry_dose_kg"]*raw["dry_coffee_inventory_mass_fraction"]*raw["availability_fraction"]
            explicit+=mass; result.append(Species(raw["id"],"explicitInventory",mass))
        else: result.append(Species(raw["id"],"structuralBalance",total-explicit))
    return result

def trace_steps(case,scenario):
    aggregate=rows(Path(case)/"postProcessing/wholePull/0/traces.csv")
    if not aggregate: raise ValueError("aggregate trace is empty")
    times=[float(r["time_s"]) for r in aggregate]
    if any(not math.isfinite(t) for t in times) or any(b<=a for a,b in zip(times,times[1:])): raise ValueError("aggregate trace times must be finite and strictly increasing")
    if not close_time(times[-1],float(scenario["time"]["end_s"]),float(scenario["time"]["delta_t_s"])): raise ValueError("trace end time does not equal run end")
    species=configured_species(scenario); indexed=species[0].species_id!="legacy_effective_solute"; by_time={}
    if indexed:
        species_rows=rows(Path(case)/"postProcessing/wholePullSpecies/0/species_traces.csv"); seen=set()
        for row in species_rows:
            key=(float(row["time_s"]),row["species_id"])
            if key in seen: raise ValueError("duplicate time/species pair")
            seen.add(key); by_time.setdefault(key[0],{})[key[1]]=float(row["cup_solute_mass_kg"])
        expected={(t,s.species_id) for t in times for s in species}
        if seen!=expected: raise ValueError("missing, extra, or misaligned species trace rows")
    previous_time=0.0; previous_water=previous_solute=0.0; previous_species={s.species_id:0.0 for s in species}; result=[]
    for row,time in zip(aggregate,times):
        water=float(row["cup_water_mass_kg"]); solute=float(row["cup_solute_mass_kg"])
        if not all(math.isfinite(v) for v in (water,solute)) or water<previous_water-1e-15 or solute<previous_solute-1e-15: raise ValueError("nonfinite or decreasing cumulative aggregate mass")
        if indexed:
            masses=[]
            for spec in species:
                value=by_time[time][spec.species_id]
                if not math.isfinite(value) or value<previous_species[spec.species_id]-1e-15: raise ValueError("nonfinite or decreasing cumulative species mass")
                masses.append(value-previous_species[spec.species_id]); previous_species[spec.species_id]=value
            if not close_mass(solute-previous_solute,sum(masses)): raise ValueError("aggregate/species step increment mismatch")
        else: masses=[solute-previous_solute]
        result.append((previous_time,time-previous_time,water-previous_water,masses,solute-previous_solute))
        previous_time=time; previous_water=water; previous_solute=solute
    return species,result

def expected(case,scenario):
    config=scenario["fractionCollection"]; species,steps=trace_steps(case,scenario)
    collector=FractionCollector(config["cumulativeBoundariesKg"],species,config["emitTerminalPartial"])
    for start,dt,water,masses,solute in steps: collector.add_step(start,dt,water,masses,solute)
    aggregate=collector.finish(); cumulative=[0.0]*len(species); long=[]
    for row in aggregate:
        beverage=row["beverage_mass_kg"]
        for i,spec in enumerate(species):
            mass=row["species_masses_kg"][i]; cumulative[i]+=mass; initial=spec.initial_inventory_kg
            long.append({"fraction_index":row["fraction_index"],"species_index":i,"species_id":spec.species_id,"species_role":spec.role,
             "species_mass_kg":mass,"species_mass_fraction_of_beverage":mass/beverage if beverage else 0.0,
             "cumulative_species_mass_kg":cumulative[i],"initial_species_inventory_kg":initial,
             "fraction_species_mass_fraction_of_initial_inventory":mass/initial if initial else 0.0,
             "cumulative_extracted_fraction_of_initial_inventory":cumulative[i]/initial if initial else 0.0})
    return aggregate,long,collector.uncompleted_boundaries

AGG_CAT=("fraction_index","status"); SPEC_CAT=("fraction_index","species_index","species_id","species_role")
AGG_MASS=("requested_lower_cumulative_beverage_mass_kg","requested_upper_cumulative_beverage_mass_kg","realized_lower_cumulative_beverage_mass_kg","realized_upper_cumulative_beverage_mass_kg","water_mass_kg","total_solute_mass_kg","beverage_mass_kg","cumulative_beverage_mass_kg","water_plus_solute_closure_residual_kg","species_sum_closure_residual_kg")
SPEC_MASS=("species_mass_kg","cumulative_species_mass_kg","initial_species_inventory_kg")
SPEC_RATIO=("species_mass_fraction_of_beverage","fraction_species_mass_fraction_of_initial_inventory","cumulative_extracted_fraction_of_initial_inventory")

def compare(case,scenario):
    wants,want_species,uncompleted=expected(case,scenario); actual=rows(Path(case)/"postProcessing/wholePullFractions/0/fractions.csv"); actual_species=rows(Path(case)/"postProcessing/wholePullFractions/0/fraction_species.csv")
    if len(actual)!=len(wants): raise AssertionError("unequal aggregate row counts")
    if len(actual_species)!=len(want_species): raise AssertionError("unequal species row counts")
    max_mass=max_time=max_ratio=0.0
    for got,want in zip(actual,wants):
        for key in AGG_CAT:
            if str(got[key])!=str(want[key]): raise AssertionError(f"aggregate identity mismatch: {key}")
        dt=max(float(got["end_time_s"])-float(got["start_time_s"]),0.0)
        for key in AGG_MASS:
            delta=abs(float(got[key])-float(want[key])); max_mass=max(max_mass,delta)
            if not close_mass(float(got[key]),float(want[key])): raise AssertionError(f"aggregate mass mismatch: {key}")
        for key in ("start_time_s","end_time_s"):
            delta=abs(float(got[key])-float(want[key])); max_time=max(max_time,delta)
            if not close_time(float(got[key]),float(want[key]),dt): raise AssertionError(f"aggregate time mismatch: {key}")
        delta=abs(float(got["tds_mass_fraction"])-float(want["tds_mass_fraction"])); max_ratio=max(max_ratio,delta)
        if delta>RATIO_ABS: raise AssertionError("aggregate ratio mismatch")
    series={}
    for got,want in zip(actual_species,want_species):
        for key in SPEC_CAT:
            if str(got[key])!=str(want[key]): raise AssertionError(f"species identity mismatch: {key}")
        for key in SPEC_MASS:
            delta=abs(float(got[key])-float(want[key])); max_mass=max(max_mass,delta)
            if not close_mass(float(got[key]),float(want[key])): raise AssertionError(f"species mass mismatch: {key}")
        for key in SPEC_RATIO:
            delta=abs(float(got[key])-float(want[key])); max_ratio=max(max_ratio,delta)
            if delta>RATIO_ABS: raise AssertionError(f"species ratio mismatch: {key}")
        series.setdefault(want["species_id"],[[],[]]); series[want["species_id"]][0].append(float(got["species_mass_kg"])); series[want["species_id"]][1].append(float(want["species_mass_kg"]))
    manifest=json.loads((Path(case)/"postProcessing/wholePullFractions/0/manifest.json").read_text())
    required={"boundary_basis":"cumulativeBeverageMass","requested_boundaries_kg":[float(x) for x in scenario["fractionCollection"]["cumulativeBoundariesKg"]],"emit_terminal_partial":scenario["fractionCollection"]["emitTerminalPartial"],"completed_fraction_count":sum(r["status"]=="complete" for r in wants),"uncompleted_requested_boundaries_kg":uncompleted,"mass_partition_convention":"piecewise_constant_step_flux_mass_partition","time_location_convention":"piecewise_constant_step_flux_mass_partition"}
    for key,value in required.items():
        if manifest.get(key)!=value: raise AssertionError(f"manifest mismatch: {key}")
    if not manifest.get("configuration_sha256") or not manifest.get("production_source_sha256"): raise AssertionError("manifest production binding absent")
    totals=manifest.get("final_emitted_cumulative_component_totals",{}); want_water=sum(r["water_mass_kg"] for r in wants); want_solute=sum(r["total_solute_mass_kg"] for r in wants)
    for key,value in (("water_mass_kg",want_water),("solute_mass_kg",want_solute),("beverage_mass_kg",want_water+want_solute)):
        if key not in totals or not close_mass(float(totals[key]),value): raise AssertionError(f"manifest cumulative total mismatch: {key}")
    metrics={}
    for sid,(got,want) in series.items():
        errors=[a-b for a,b in zip(got,want)]; denom=max(max(map(abs,want),default=0.0),MASS_ABS)
        metrics[sid]={"nrmse":math.sqrt(sum(e*e for e in errors)/len(errors))/denom if errors else 0.0,"endpoint_relative":abs(sum(got)-sum(want))/max(abs(sum(want)),MASS_ABS)}
    return {"status":"PASS","maximum_mass_error_kg":max_mass,"maximum_time_error_s":max_time,"maximum_ratio_error":max_ratio,"species_metrics":metrics,"aggregate_rows":len(actual),"species_rows":len(actual_species)}
