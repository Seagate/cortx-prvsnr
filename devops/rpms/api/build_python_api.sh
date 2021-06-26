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
repo_root_dir="$(realpath $script_dir/../../../)"
docker_image_name="seagate/cortx-prvsnr:fpm"

in_docker=false
input_dir_api="$repo_root_dir/api/python"
input_dir_lrcli="$repo_root_dir/lr-cli"
output_dir=.
output_type=rpm
fpm_tool_api=fpm
fpm_tool_lrcli=fpm
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
    local _long_opts=help,docker,out-dir:,out-type:,fpm-tool:,pkg-ver:,verbose

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
                fpm_tool_api="$2"
                fpm_tool_lrcli="$2"
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
    parsed_args+="\n\tfpm_tool=$fpm_tool\n\tverbosity=$verbosity"
    parsed_args+="\n\trelease=$pkg_version"

    echo -e "Parsed arguments:\n$parsed_args"
fi


iteration=
if [[ -n "$pkg_version" ]]; then
    iteration="--iteration $pkg_version"
fi

tmp_dir_api="$(mktemp -d)"
cp -r "${input_dir_api}/." "${tmp_dir_api}"
input_dir_api="$tmp_dir_api"

tmp_dir_lrcli="$(mktemp -d)"
cp -r "${input_dir_lrcli}/." "${tmp_dir_lrcli}"
input_dir_lrcli="$tmp_dir_lrcli"

pushd "$output_dir"
    rm -f python3*-cortx-prvsnr*
popd

if [[ "$in_docker" == true ]]; then
    docker_build_dir_api="${tmp_dir_api}/docker"
    docker_build_dir_lrcli="${tmp_dir_lrcli}/docker"

    pushd $script_dir
        mkdir "$docker_build_dir_api"
        cp "${repo_root_dir}/images/docker/setup_fpm.sh" Dockerfile "$docker_build_dir_api"
        docker build -t $docker_image_name "$docker_build_dir_api"

        mkdir "$docker_build_dir_lrcli"
        cp "${repo_root_dir}/images/docker/setup_fpm.sh" Dockerfile "$docker_build_dir_lrcli"
        docker build -t $docker_image_name "$docker_build_dir_lrcli"
    popd

    input_dir_api="$(realpath $input_dir_api)"
    output_dir="$(realpath $output_dir)"
    fpm_tool_api="docker run --rm -u $(id -u):$(id -g) -v $input_dir_api:/tmp/in_api -v $output_dir:/tmp/out $docker_image_name"
    input_dir_api="/tmp/in_api"
    output_dir="/tmp/out"

    input_dir_lrcli="$(realpath $input_dir_lrcli)"
    output_dir="$(realpath $output_dir)"
    fpm_tool_lrcli="docker run --rm -u $(id -u):$(id -g) -v $input_dir_lrcli:/tmp/in_lrcli -v $output_dir:/tmp/out $docker_image_name"
    input_dir_lrcli="/tmp/in_lrcli"
    output_dir="/tmp/out"

fi
    # FIXME 'python-disable-dependency' params
    #       are dirty hacks just to quickly resolve issues
    #       that depends on other Cortx components, need to
    #       remove later
    # --depends "salt >= 3002" \
echo -e "Packaging api directory"
$fpm_tool_api --input-type "python" \
    --output-type "$output_type" \
    --architecture "amd64" \
    --verbose \
    --python-install-lib "/usr/lib/python3.6/site-packages" \
    --python-install-bin "/usr/bin" \
    --python-package-name-prefix "python36" \
    --python-bin "python3" \
    --python-disable-dependency salt \
    --python-disable-dependency Jinja2 \
    --no-python-downcase-dependencies \
    --exclude "*.pyc" \
    --exclude "*.pyo" \
    --rpm-auto-add-directories \
    --before-install "$input_dir_api/provisioner/srv/salt/provisioner/files/pre_setup.sh" \
    --after-install "$input_dir_api/provisioner/srv/salt/provisioner/files/post_setup.sh" \
    --package "${output_dir}" \
    $iteration \
    "${input_dir_api}"

echo -e "Packaging lr-cli directory"
$fpm_tool_lrcli --input-type "python" \
    --output-type "$output_type" \
    --architecture "amd64" \
    --verbose \
    --python-install-lib "/usr/lib/python3.6/site-packages" \
    --python-install-bin "/usr/bin" \
    --python-package-name-prefix "python36" \
    --python-bin "python3" \
    --python-disable-dependency salt \
    --python-disable-dependency Jinja2 \
    --no-python-downcase-dependencies \
    --exclude "*.pyc" \
    --exclude "*.pyo" \
    --rpm-auto-add-directories \
    --package "${output_dir}" \
    $iteration \
    "${input_dir_lrcli}"



# TODO remove it anyway even if some upper fails (kind of finally routine)
rm -rf "${tmp_dir_api}"
rm -rf "${tmp_dir_lrcli}"

# TODO other options if needed
#    --depends
#    --before-install
#    --before-remove
#    --name
