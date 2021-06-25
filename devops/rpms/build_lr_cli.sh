#!/bin/bash
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#


set -eu

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
repo_root_dir="$(realpath "$script_dir/../../")"
docker_image_name="seagate/cortx-prvsnr:fpm"

in_docker=false
input_dir="$repo_root_dir/lr-cli"
output_dir=.
output_type=rpm
fpm_tool=fpm
pkg_version=
verbosity=0


function usage {
  echo "\
Usage: $0 [options]

Builds provisioner API package using fpm tool

Options:
  -d,  --docker         build using docker,
                            default: $in_docker
       --fpm-tool       fpm tool path or docker image name,
                            default: $fpm_tool
  -h,  --help           print this help and exit
  -i,  --in-dir DIR     path to provisioner API directory,
                            default: $input_dir
  -o,  --out-dir DIR    output dir,
                            default: $output_dir
  -r,  --pkg-ver        package version (release tag),
                            default: $pkg_version
  -t,  --out-type       output package type. Possible values: {rpm|deb|...}
                            default: $output_type,
                            check https://github.com/jordansissel/fpm/wiki#usage
  -v,  --verbose        be more verbose
"
}

function parse_args {
    set -eu

    ! getopt --test > /dev/null
    if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
        >&2 echo 'Error: getopt is not functional.'
        exit 1
    fi

    local _opts=hdi:o:t:r:v
    local _long_opts=help,docker,in-dir:,out-dir:,out-type:,fpm-tool:,pkg-ver:,verbose

    local _getopt_res
    ! _getopt_res=$(getopt --name "$0" --options=$_opts --longoptions=$_long_opts -- "$@")
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        exit 2
    fi

    # TODO why eval here
    eval set -- "$_getopt_res"

    while true; do
        case "$1" in
            -h|--help)
                usage
                exit 0
                ;;
            -d|--docker)
                in_docker=true
                shift
                ;;
            -i|--in-dir)
                input_dir="$2"
                if [[ ! -d "$input_dir" ]]; then
                    >&2 echo "'$input_dir' not a directory"
                    exit 5
                fi
                shift 2
                ;;
            -o|--out-dir)
                output_dir="$2"
                if [[ ! -d "$output_dir" ]]; then
                    >&2 echo "'$output_dir' not a directory"
                    exit 5
                fi
                shift 2
                ;;
            -t|--out-type)
                output_type="$2"
                # TODO check possible values
                shift 2
                ;;
            --fpm-tool)
                fpm_tool="$2"
                shift 2
                ;;
            -r|--pkg-ver)
                pkg_version="$2"
                shift 2
                ;;
            -v|--verbose)
                ((verbosity=verbosity+1))
                shift
                ;;
            --)
                shift
                break
                ;;
            ?)
                >&2 echo "Runtime error"
                exit 3
                ;;
            *)
                >&2 echo "Parser error"
                exit 3
        esac
    done
}


parse_args "$@"

if [[ "$verbosity" -ge 2 ]]; then
    set -x
fi

if [[ "$verbosity" -ge 1 ]]; then
    parsed_args=""
    parsed_args+="\toutput_dir=$output_dir\n\toutput_type=$output_type"
    parsed_args+="\n\tin_docker=$in_docker\n\tinput_dir=$input_dir"
    parsed_args+="\n\tfpm_tool=$fpm_tool\n\tverbosity=$verbosity"
    parsed_args+="\n\trelease=$pkg_version"

    echo -e "Parsed arguments:\n$parsed_args"
fi


iteration=()
if [[ -n "$pkg_version" ]]; then
    iteration+=("--iteration" "$pkg_version")
fi

tmp_dir="$(mktemp -d)"
cp -r "${input_dir}/." "${tmp_dir}"
input_dir="$tmp_dir"

pushd "$output_dir"
    rm -f python3*-cortx_setup*
popd

if [[ "$in_docker" == true ]]; then
    docker_build_dir="${tmp_dir}/docker"

    pushd "$script_dir"
        mkdir "$docker_build_dir"
        cp "${repo_root_dir}/images/docker/setup_fpm.sh" api/Dockerfile "$docker_build_dir"
        docker build -t $docker_image_name "$docker_build_dir"
    popd

    input_dir="$(realpath "$input_dir")"
    output_dir="$(realpath "$output_dir")"
    fpm_tool="docker run --rm -u $(id -u):$(id -g) -v $input_dir:/tmp/in -v $output_dir:/tmp/out $docker_image_name"
    input_dir="/tmp/in"
    output_dir="/tmp/out"
fi

$fpm_tool --input-type "python" \
    --output-type "$output_type" \
    --architecture "amd64" \
    --verbose \
    --python-install-lib "/usr/lib/python3.6/site-packages" \
    --python-install-bin "/usr/bin" \
    --python-package-name-prefix "python36" \
    --python-bin "python3" \
    --no-python-downcase-dependencies \
    --exclude "*.pyc" \
    --exclude "*.pyo" \
    --rpm-auto-add-directories \
    --package "${output_dir}" \
    "${iteration[@]}" \
    "${input_dir}"


# TODO remove it anyway even if some upper fails (kind of finally routine)
rm -rf "${tmp_dir}"

# TODO other options if needed
#    --depends
#    --before-install
#    --before-remove
#    --name
