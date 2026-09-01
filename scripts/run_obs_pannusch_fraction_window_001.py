#!/usr/bin/env python3
import pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from analysis.obs_pannusch_fraction_window_001.run import main
if __name__=="__main__": main()

