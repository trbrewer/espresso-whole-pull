from __future__ import annotations
import hashlib, subprocess
from pathlib import Path
from . import STOP_AUTHORITY

COMMIT="a3428a4d4ad571ef3168a70e8a04620fca5d3520"
TREE="6175b4ad39f45ebcdec32a176e5611bf3b03655b"
FILES={
"docs/cards/wadsworth2026_grindmap.md":"8cffbac5fe9f42072fb880be8b9e972870c847386eacd0ed2091d6f3dd1c34d4",
"docs/cards/wadsworth2026.md":"606abfce68ba40105b4650ee6af2e8c716c60adb2653b87065b5fd2207c25fe8",
"puckworks/data/wadsworth2026/wadsworth2026_table1_full.csv":"3b0139fe02108d3dfcd1441d9e4062e86d9b7e1a8505141a7beefd9366ebf20f",
"puckworks/data/wadsworth2026/PROVENANCE.md":"7cd0903f3e3e14b5172eecdcb0aff1a34177b0b85f7fd504dba63592804efe16",
"docs/cards/vacaguerra2023a.md":"d2c5e0877578336210d96e15749ed8eea0fd7d910be636e07010b056639e7a30",
"puckworks/data/vacaguerra2023a/PROVENANCE.md":"f36c1371ae5c73e64ec918494086d715a4d8d8452350caa8eb7fffc60f253c32",
"puckworks/data/vacaguerra2023a/Figure_12_Calculated_versus_experimental_dry_bed_porosity_validation_experiments.csv":"bb5c59eefc955c48ebeb79c6c25967831cb250d3d1d489c634c2e8d78f6f380c",
"puckworks/data/vacaguerra2023a/Table_1_Particle_size_distributions_used_in_extraction_experiments.csv":"7df7a39c7c3de164a9b12f8fccbe39b4f5b27f0904ad9b863a6803112641b1a5",
"puckworks/data/vacaguerra2023a/Table_2_Empirical_coefficients_compression_factor_phi_Equation_9.csv":"a5f6abe29ee1257420f7c35bd9f4233262ee700575b6f13a7b5b94391bacfb6d",
"puckworks/data/vacaguerra2023a/Table_3_Empirical_coefficients_compression_factor_omega_Equation_10.csv":"170c724cb6142eedf6fe8d0f994559d3dcc4261443445892d62e8d6ffebca7d9",
"puckworks/data/vacaguerra2023a/Table_C1_Extraction_conditions_from_permeability_experiments.csv":"08f175fffd7895f673bc2868c116454ba517263059195cb2d51b4356efb1e44f"}
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def verify(root:Path)->dict:
    try:
        commit=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
        tree=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD^{tree}"],text=True).strip()
        actual={p:sha(root/p) for p in FILES}
    except Exception as e: raise RuntimeError(f"{STOP_AUTHORITY}: {e}") from e
    bad={p:[FILES[p],actual.get(p)] for p in FILES if actual.get(p)!=FILES[p]}
    if commit!=COMMIT or tree!=TREE or bad:
        raise RuntimeError(f"{STOP_AUTHORITY}: commit={commit} tree={tree} bad={bad}")
    manifest=(root/"puckworks/data/MANIFEST.csv").read_text()
    if "wadsworth2026_table1" not in manifest or "wadsworth2026/table1_full" not in manifest:
        raise RuntimeError(f"{STOP_AUTHORITY}: MANIFEST family missing")
    return {"commit":commit,"tree":tree,"files":actual,"permeability_card_path":"docs/cards/wadsworth2026.md","rights":{"wadsworth":"CC-BY-4.0_OPEN_ACCESS","vaca":"PREPRINT_TRANSCRIPTION_ANALYSIS_ONLY_NO_PUBLISHER_PDF_REDISTRIBUTION"}}
