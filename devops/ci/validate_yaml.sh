#!/bin/bash

set -eu
set -o pipefail

# TODO make that configurable
out_file=yamllint.out

targets="${1:-}"

yamllint --format parsable $targets 2>&1 | tee "$out_file"
