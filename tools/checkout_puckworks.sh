#!/usr/bin/env bash
set -euo pipefail

readonly repository_url="https://github.com/trbrewer/puckworks.git"
readonly locked_commit="352dacd51015d95a3b5a5b3e1a8fb331419d78b0"

if [[ $# -ne 1 ]]; then
    echo "usage: $0 DESTINATION" >&2
    exit 2
fi

readonly destination="$1"
if [[ -e "$destination" ]]; then
    echo "refusing existing destination: $destination" >&2
    exit 2
fi

git clone --no-checkout "$repository_url" "$destination"
git -C "$destination" checkout --detach "$locked_commit"
test "$(git -C "$destination" rev-parse HEAD)" = "$locked_commit"
test -z "$(git -C "$destination" status --porcelain)"
printf 'Puckworks checkout verified at %s\n' "$locked_commit"
