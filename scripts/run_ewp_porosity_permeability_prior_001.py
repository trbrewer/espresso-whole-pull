#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from analysis.ewp_porosity_permeability_prior_001.run import main
raise SystemExit(main())
