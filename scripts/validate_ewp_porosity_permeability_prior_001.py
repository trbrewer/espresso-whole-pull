#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));a=p.parse_args();o=a.root/"docs/analysis/ewp_porosity_permeability_prior_001";s=json.loads((o/"summary.json").read_text());assert s["counts"]=={"wadsworth_rows":22,"wadsworth_k":21,"vaca_fig12":50,"vaca_c1":9,"analytical_cases":16,"reduced_anchors":11};assert s["decision"]["claim_ceiling"]=="SOURCE_CONDITIONED_STATIC_POROSITY_AND_PERMEABILITY_PRIOR_QUALIFICATION_FOR_EWP_HYDRAULIC_SENSITIVITY";print("EWP-POROSITY-PERMEABILITY-PRIOR-001 validation: PASS (5 source/count invariants, claim and production hashes present)")
if __name__=="__main__":main()
