#!/bin/bash

set -eux

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
repo_root_dir="$(realpath $script_dir/../../../)"
docker_image_name="seagate/ees-prvsnr:fpm"

def_output_path=.
def_output_type=rpm
def_input_path="$repo_root_dir/api/python"
def_in_docker=true
def_fpm_tool="fpm"

function usage {
  echo "\
Usage: $0 [-h|--help] [<output-path> [<output-type> [<input-path> [in-docker [<fpm-tool>]]]]]
    
  output-path   :  output dir, default: $def_output_path
  output-type   :  output package type. Possible values: {rpm|deb|...}
                   (check https://github.com/jordansissel/fpm/wiki#usage), default: $def_output_type
  input-path    :  input dir, default: $def_input_path
  in-docker     :  build using docker, default: $def_in_docker
  fpm-tool      :  fpm tool path or docker image name, default: $def_fpm_tool
"
}

output_path="${1:-$def_output_path}"
output_type="${2:-$def_output_type}"
input_path="${3:-$def_input_path}"
in_docker="${4:-$def_in_docker}"
fpm_tool="${5:-$def_fpm_tool}"

first_arg="${1:-}"
if [[ "$first_arg" == '-h' || "$first_arg" == '--help' ]]; then
    usage
    exit 0
fi

iteration="${RPM_RELEASE:-}"
if [[ -n "$iteration" ]]; then
    iteration="--iteration $iteration"
fi

tmp_dir="$(mktemp -d)"
cp -r "${input_path}/." "${tmp_dir}"
input_path="$tmp_dir"

pushd $input_path
    sed -i "s~PyYAML~python36-PyYAML~" setup.py
popd

if [[ "$in_docker" == true ]]; then
    pushd $script_dir
        docker build -t $docker_image_name .
    popd

    input_path="$(realpath $input_path)"
    output_path="$(realpath $output_path)"
    fpm_tool="docker run --rm -u $(id -u):$(id -g) -v $input_path:/tmp/in -v $output_path:/tmp/out $docker_image_name"
    input_path="/tmp/in"
    output_path="/tmp/out"
fi

$fpm_tool --input-type "python" \
    --output-type "$output_type" \
    --architecture "amd64" \
    --verbose \
    --python-install-lib "/usr/lib/python3.6/site-packages" \
    --python-package-name-prefix "python3" \
    --python-bin "python3" \
    --exclude "*.pyc" \
    --exclude "*.pyo" \
    --no-python-fix-dependencies \
    --no-python-downcase-dependencies \
    --package "${output_path}" \
    $iteration \
    "${input_path}"

# TODO remove it anyway even if some upper fails (kind of finally routine)
rm -rf "${tmp_dir}"

# TODO other options if needed
#    --depends
#    --before-install
#    --after-install
#    --before-remove
#    --name
#    --python-bin
