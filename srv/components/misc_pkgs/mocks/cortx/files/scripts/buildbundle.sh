#!/bin/bash

set -eu

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cortx_version=1.0.0
output_dir=.
output_type=deploy-cortx
verbosity=0
gen_iso=false

tmp_dir=
cmd_prefix="bash"

function trap_handler_exit {
    ret=$?

    if [[ -n "$tmp_dir" ]]; then
        rm -rf "$tmp_dir"
    fi

    if [[ $ret -ne 0 ]]; then
        echo "***** FAILED!! *****"
        echo "Exiting with return code: $ret"
    else
        echo "Exiting with return code: $ret"
    fi
}
trap trap_handler_exit EXIT


function usage {
  echo "\
Usage: $0 [options]

Builds provisioner API package using fpm tool

Options:
  -h,  --help           print this help and exit
  -o,  --out-dir DIR    output dir,
                            default: $output_dir
  -r,  --cortx-ver      cortx release version,
                            default: $cortx_version
  -t,  --out-type       output bundle type. Possible values: {deploy-cortx|deploy-single|upgrade}
                            default: $output_type,
  -v,  --verbose        be more verbose
       --gen-iso        generate ISO
"
}

function parse_args {
    set -eu

    ! getopt --test > /dev/null
    if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
        >&2 echo 'Error: getopt is not functional.'
        exit 1
    fi

    local _opts=ho:r:t:v
    local _long_opts=help,out-dir:,out-type:,cortx-ver:,verbose,gen-iso

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
            -o|--out-dir)
                output_dir="$2"
                if [[ -e "$output_dir" ]]; then
                    if [[ ! -d "$output_dir" ]]; then
                        >&2 echo "'$output_dir' not a directory"
                        exit 5
                    fi
                else
                    mkdir -p "$output_dir"
                fi
                shift 2
                ;;
            -r|--cortx-ver)
                cortx_version="$2"
                shift 2
                ;;
            -t|--out-type)
                output_type="$2"
                # TODO check possible values
                shift 2
                ;;
            -v|--verbose)
                ((verbosity=verbosity+1))
                shift
                ;;
            --gen-iso)
                gen_iso=true
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
    cmd_prefix="bash -x"
fi

if [[ "$verbosity" -ge 1 ]]; then
    parsed_args=""
    parsed_args+="\toutput_dir=$output_dir\n\toutput_type=$output_type"
    parsed_args+="\n\tverbosity=$verbosity"
    parsed_args+="\n\trelease=$cortx_version\n\tgen-iso=$gen_iso"

    echo -e "Parsed arguments:\n$parsed_args"
fi


for pkg in rpm-build rpmdevtools createrepo genisoimage
do
    rpm --quiet -qi "$pkg" || yum install -q -y "$pkg" && echo "$pkg already installed."
done

tmp_dir="$(mktemp -d)"
build_dir="$tmp_dir"

echo -e "Building CORTX rpms, build dir: $build_dir"
$cmd_prefix "${script_dir}/buildrpm.sh" "$cortx_version" "$build_dir"

echo -e "Preparing a $output_type bundle, output dir: $output_dir"
pushd "$output_dir"
    rpms_dir="${build_dir}/rpmbuild/RPMS/noarch/"
    release_info="RELEASE.INFO"

    if [[ "$output_type" == "deploy-cortx" ]]; then
        cp -r "${rpms_dir}"/* .
        yum_repos=.
    else
        yum_repos=("cortx_iso" "3rd_party")

        if [[ "$output_type" == "upgrade" ]]; then
            yum_repos+=("os")
        fi

        mkdir python_deps "${yum_repos[@]}"
        cp -r "${rpms_dir}"/* cortx_iso
    fi

    for repo in "${yum_repos[@]}"; do
        createrepo "$repo"
    done

    echo -e "Preparing a release info data"
    sed_cmds="s/{{ VERSION }}/$cortx_version/g"
    sed_cmds+="; s/{{ DATE }}/$(LC_ALL=en_US.UTF-8 date --utc)/g"
    sed_cmds+="; s/{{ KERNEL }}/$(uname -r)/g"
    sed "$sed_cmds" "${script_dir}/../${release_info}" >"$release_info"
    pkgs="$(find "$rpms_dir" -name '*.rpm' -type f -printf "%f\n")"
    for pkg in $pkgs; do
        echo "- $pkg" >>"$release_info"
    done

if [[ "$gen_iso" == true ]]; then
    rm -rf "$output_dir.iso"
    mkisofs -graft-points -r -l -iso-level 2 -J -o "$output_dir.iso" "$output_dir"
fi
