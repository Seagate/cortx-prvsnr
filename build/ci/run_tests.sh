#!/bin/bash

set -eu
set -o pipefail

# TODO make that configurable
out_file=pytest.out

pytest_args="$@"

python -m pytest $pytest_args 2>&1 | tee "$out_file"
