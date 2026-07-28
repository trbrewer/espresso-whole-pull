#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 DESTINATION" >&2
    exit 2
fi

readonly destination="$1"
readonly script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly repository_root="$(cd -- "${script_dir}/.." && pwd -P)"
readonly lock_path="${repository_root}/dependencies/puckworks.lock.json"
readonly canonical_repository_url="https://github.com/trbrewer/puckworks.git"

if [[ ! -f "$lock_path" ]]; then
    echo "Puckworks lock is missing: $lock_path" >&2
    exit 2
fi

lock_values="$(
    python3 - "$lock_path" "$canonical_repository_url" <<'PY'
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

lock_path = Path(sys.argv[1])
canonical_url = sys.argv[2]
try:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
except (OSError, UnicodeError, json.JSONDecodeError) as exc:
    raise SystemExit(f"invalid Puckworks lock: {exc}")

required = {
    "schema_version",
    "repository_url",
    "checkout_commit",
    "checkout_tree_sha",
    "submodule",
    "vendored",
}
missing = sorted(required - lock.keys())
if missing:
    raise SystemExit(f"Puckworks lock missing required fields: {', '.join(missing)}")
if lock["schema_version"] != "espresso.public.puckworks_lock.v2":
    raise SystemExit(f"unsupported Puckworks lock schema: {lock['schema_version']!r}")

url = lock["repository_url"]
if not isinstance(url, str):
    raise SystemExit("Puckworks repository_url must be a string")
parsed = urlsplit(url)
if parsed.username is not None or parsed.password is not None:
    raise SystemExit("credential-bearing Puckworks repository URL is forbidden")
if url != canonical_url:
    raise SystemExit(f"unexpected Puckworks repository URL: {url!r}")

commit = lock["checkout_commit"]
tree = lock["checkout_tree_sha"]
if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
    raise SystemExit("Puckworks checkout_commit must be exactly 40 lowercase hexadecimal characters")
if not isinstance(tree, str) or re.fullmatch(r"[0-9a-f]{40}", tree) is None:
    raise SystemExit("Puckworks checkout_tree_sha must be exactly 40 lowercase hexadecimal characters")
if lock["submodule"] is not False or lock["vendored"] is not False:
    raise SystemExit("Puckworks lock must declare non-submodule, non-vendored integration")

print(url)
print(commit)
print(tree)
PY
)"
mapfile -t parsed_lock <<<"$lock_values"
if [[ ${#parsed_lock[@]} -ne 3 ]]; then
    echo "invalid Puckworks lock parser output" >&2
    exit 2
fi
readonly repository_url="${parsed_lock[0]}"
readonly locked_commit="${parsed_lock[1]}"
readonly locked_tree="${parsed_lock[2]}"

if [[ -e "$destination" ]]; then
    echo "refusing existing destination: $destination" >&2
    exit 2
fi

GIT_TERMINAL_PROMPT=0 GIT_LFS_SKIP_SMUDGE=1 \
    git -c core.hooksPath=/dev/null clone \
    --no-checkout \
    --no-recurse-submodules \
    "$repository_url" \
    "$destination"
GIT_TERMINAL_PROMPT=0 GIT_LFS_SKIP_SMUDGE=1 \
    git -c core.hooksPath=/dev/null -C "$destination" checkout --detach "$locked_commit"

if [[ "$(git -C "$destination" rev-parse HEAD)" != "$locked_commit" ]]; then
    echo "Puckworks checkout commit verification failed" >&2
    exit 1
fi
if [[ "$(git -C "$destination" rev-parse HEAD^{tree})" != "$locked_tree" ]]; then
    echo "Puckworks checkout tree verification failed" >&2
    exit 1
fi
if git -C "$destination" symbolic-ref -q HEAD >/dev/null; then
    echo "Puckworks checkout is not detached" >&2
    exit 1
fi
if [[ -n "$(git -C "$destination" status --porcelain=v1)" ]]; then
    echo "Puckworks checkout is not clean" >&2
    exit 1
fi
if git -C "$destination" ls-files --stage | awk '$1 == "160000" { found = 1 } END { exit !found }'; then
    echo "Puckworks checkout contains a gitlink; submodule initialization is forbidden" >&2
    exit 1
fi

printf 'Puckworks checkout verified at commit %s tree %s\n' "$locked_commit" "$locked_tree"
