"""One-way CSV allowlist sanitizer. Source rows are never logged."""
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path

def sanitize(inp,out:Path,columns:tuple[str,...])->dict:
    reader=csv.DictReader(inp)
    if reader.fieldnames is None or len(reader.fieldnames)!=len(set(reader.fieldnames)):
        raise ValueError("malformed or duplicate source header")
    if len(columns)!=len(set(columns)) or any(c not in reader.fieldnames for c in columns):
        raise ValueError("missing or duplicate allowed column")
    tmp=out.with_suffix(out.suffix+'.tmp'); count=0
    with tmp.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
        for row in reader:
            if None in row or any(row[c] is None for c in columns):raise ValueError("malformed CSV row")
            w.writerow({c:row[c] for c in columns});count+=1
    tmp.replace(out)
    return {'schema':list(columns),'row_count':count,'sanitized_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--columns',required=True);p.add_argument('--metadata',type=Path,required=True)
    a=p.parse_args(argv); cols=tuple(a.columns.split(',')); meta=sanitize(sys.stdin,a.output,cols);a.metadata.write_text(json.dumps(meta,sort_keys=True,indent=2)+'\n');return 0
if __name__=='__main__':raise SystemExit(main())
