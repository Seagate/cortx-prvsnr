#!/bin/bash

set -eu
set -o pipefail

# TODO make that configurable

args="${1:-}"
marker_expr="${2:-}"
out_file="${3:-pytest.out}"

cmd="python -m pytest $args"

if [[ -n "$marker_expr" ]]; then
    cmd="$cmd -m '$marker_expr'"
fi

bash -c "$cmd" 2>&1 | tee "$out_file"
