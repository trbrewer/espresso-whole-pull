#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));a=p.parse_args();o=a.root/"docs/analysis/ewp_porosity_permeability_prior_001";s=json.loads((o/"summary.json").read_text());c=s["counts"];assert (c["wadsworth_rows"],c["wadsworth_k"],c["wadsworth_observed_pairs"],c["vaca_fig12"],c["vaca_c1"],c["vaca_observed_pair_representations"],c["factorial_cases"],c["pressure_cases"],c["convergence_rows"])==(22,21,21,50,9,18,27,15,12);assert s["decision"]["code"]=="EWP_POROSITY_PERMEABILITY_PRIOR_001_POSITIVE_POROSITY_ONLY";assert s["decision"]["gate_inputs"]["eligible_permeability_supports"]==0;assert s["decision"]["claim_ceiling"]=="SOURCE_CONDITIONED_STATIC_POROSITY_AND_PERMEABILITY_PRIOR_QUALIFICATION_FOR_EWP_HYDRAULIC_SENSITIVITY";print("EWP-POROSITY-PERMEABILITY-PRIOR-001 C1 validation: PASS (source, pair, factorial, pressure, convergence, decision and claim gates)")
if __name__=="__main__":main()
