#!/bin/bash

set -eu

# TODO make that configurable
out_file=flake8.out

targets="${1:-}"

python -m flake8 --output-file="$out_file" --tee $targets
