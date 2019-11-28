#!/bin/bash

set -eu
set -o pipefail

out_file="${1:-pipenv.out}"

pipenv --three 2>&1 | tee "$out_file"
pipenv run pip install -r test-requirements.txt 2>&1 | tee "$out_file"
