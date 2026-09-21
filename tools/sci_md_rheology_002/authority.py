"""Explicit post-result software amendments; the prospective freeze is immutable."""
import json
from tools.sci_md_rheology_001.analysis import sha


def expected(doc):
    freeze=json.loads((doc/'FREEZE.json').read_text())
    files=dict(freeze['files']);executable=freeze['executable_sha256']
    path=doc/'POST_RESULT_AMENDMENT.json'
    if path.exists():
        amendment=json.loads(path.read_text())
        if amendment['original_freeze_sha256']!=sha(doc/'FREEZE.json'):
            raise ValueError('amendment targets another freeze')
        for name,change in amendment['files'].items():
            if files.get(name)!=change['original_sha256']:
                raise ValueError('amendment original hash mismatch')
            files[name]=change['amended_sha256']
        if amendment['original_executable_sha256']!=executable:
            raise ValueError('amendment original executable mismatch')
        executable=amendment['qualified_executable_sha256']
    return freeze,files,executable
