"""Verify retained receipts only. No preparation of native cases or execution."""
import argparse
import json
from pathlib import Path
from .observe import DOC, ROOT, sha


def retained_cases(art):
    old=Path(json.loads((art/'LOCATIONS.json').read_text())['accepted'])
    receipt=json.loads((ROOT/'docs/analysis/sci_md_rheology_009/ARTIFACT_RECEIPT.json').read_text())
    if sha(old/'full/INVOCATIONS.jsonl')!=receipt['ledgers']['full']:raise ValueError('009 ledger identity')
    receipt=json.loads((ROOT/'docs/analysis/sci_md_rheology_010/ARTIFACT_RECEIPT.json').read_text())
    if sha(art/'ATTEMPTS.jsonl')!=receipt['ledger_sha256']:raise ValueError('010 ledger identity')
    expected=json.loads((ROOT/'docs/analysis/sci_md_rheology_010/SECTIONS.json').read_text())['cases']
    result={};missing={}
    for name in sorted(expected):
        config,slot=name.split('_',1);root=old if config=='old' else art
        ledger=root/('full/INVOCATIONS.jsonl' if config=='old' else 'ATTEMPTS.jsonl')
        events=[json.loads(x) for x in ledger.read_text().splitlines()]
        try:
            events=[e for e in events if e['slot']==slot and e['status']=='COMPLETE']
            if len(events)!=1:raise ValueError('unique accepted completion missing')
            e=events[0];directory=root/('full' if config=='old' else 'runs')/e['id']
            for file,h in e['files'].items():
                if sha(directory/file)!=h:raise ValueError('retained artifact changed '+file)
            scenario=json.loads((directory/'scenario.json').read_text())
            if sha(directory/'scenario.json')!=expected[name]['scenario_sha256']:raise ValueError('scenario hash')
            result[name]=(directory/'case',scenario)
        except (OSError,ValueError,KeyError) as error:missing[name]=str(error).replace(str(root),'<retained-root>')
    return result,missing


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args()
    cases,missing=retained_cases(a.artifacts)
    print(json.dumps(dict(verified_cases=sorted(cases),missing=missing,native_integrations=0)))

if __name__=='__main__':main()
