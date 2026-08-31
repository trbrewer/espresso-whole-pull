from __future__ import annotations
import csv,json
from pathlib import Path
def jsonout(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+"\n")
def csvout(p,rows,fields=None):
 rows=list(rows);fields=fields or sorted({k for r in rows for k in r});
 with p.open("w",newline="") as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
