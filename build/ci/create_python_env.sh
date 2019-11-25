#!/bin/bash

set -eu

pipenv --three
pipenv run pip install -r test-requirements.txt
