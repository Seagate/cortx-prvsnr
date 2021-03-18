#!/bin/bash

set -eu

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cortx_version=2.0.0
orig_iso=
output_dir=.
output_type=deploy-cortx
verbosity=0
gen_iso=false
prvsnr_pkg=
prvsnr_api_pkg=

tmp_dir=
orig_bundle=
cmd_prefix="bash"

function trap_handler_exit {
    ret=$?

    if [[ -d "$orig_bundle" ]]; then
        umount "$orig_bundle" || true
    fi

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

Builds different types of CORTX distribution.

The type of a distribution, release version and output directory
can be configured.

If location of an original Cortx single repo image is specified
(using '--orig-iso') then EPEL-7, SaltStack and GlusterFS repositories
along with provisioner release packages would be copied from the ISO
to a new bundle.

Custom provisioner packages might be packed inside a bundle using
'--prvsnr-pkg' and '--prvsnr-api-pkg' options.

Finally if '--gen-iso' is specified then an ISO file is generated as well.

Options:
  -h,  --help                   print this help and exit
  -i,  --orig-iso FILE          original ISO for partial use,
                                    default: $orig_iso
  -o,  --out-dir DIR            output dir,
                                    default: $output_dir
  -r,  --cortx-ver              cortx release version,
                                    default: $cortx_version
  -t,  --out-type               output type. Possible values: {deploy-cortx|deploy-single|upgrade}
                                    default: $output_type,
  -v,  --verbose                be more verbose
       --gen-iso                generate ISO
       --prvsnr-pkg FILE        provisioner package location
                                    default: $prvsnr_pkg
       --prvsnr-api-pkg FILE    provisioner api package location
                                    default: $prvsnr_api_pkg
"
}


function check_file {
    local _file="$1"
    if [[ ! -f "$_file" ]]; then
        >&2 echo "'$_file' not a file"
        exit 5
    fi
}

function check_file_exists {
    local _file="$1"
    if [[ ! -e "$_file" ]]; then
        >&2 echo "no file '$_file'"
        exit 5
    else
        check_file "$_file"
    fi
}


function parse_args {
    set -eu

    ! getopt --test > /dev/null
    if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
        >&2 echo 'Error: getopt is not functional.'
        exit 1
    fi

    local _opts=hi:o:r:t:v
    local _long_opts=help,orig-iso:,out-dir:,out-type:,cortx-ver:,verbose,gen-iso,prvsnr-pkg:,prvsnr-api-pkg:

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
            -i|--orig-iso)
                orig_iso="$2"
                check_file_exists "$orig_iso"
                shift 2
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
            --prvsnr-pkg)
                prvsnr_pkg="$2"
                check_file_exists "$prvsnr_pkg"
                shift 2
                ;;
            --prvsnr-api-pkg)
                prvsnr_api_pkg="$2"
                check_file_exists "$prvsnr_api_pkg"
                shift 2
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
    parsed_args+="\torig_iso=$orig_iso"
    parsed_args+="\n\toutput_dir=$output_dir\n\toutput_type=$output_type"
    parsed_args+="\n\tverbosity=$verbosity"
    parsed_args+="\n\trelease=$cortx_version\n\tgen-iso=$gen_iso"
    parsed_args+="\n\tprvsnr_pkg=$prvsnr_pkg\n\tprvsnr_api_pkg=$prvsnr_api_pkg"

    echo -e "Parsed arguments:\n$parsed_args"
fi


for pkg in rpm-build rpmdevtools createrepo genisoimage
do
    rpm --quiet -qi "$pkg" || yum install -q -y "$pkg" && echo "$pkg already installed."
done

tmp_dir="$(mktemp -d)"
build_dir="$tmp_dir"

release_info="RELEASE.INFO"

echo -e "Building CORTX rpms, build dir: $build_dir"
$cmd_prefix "${script_dir}/buildrpm.sh" "$cortx_version" "$build_dir"

echo -e "Preparing a $output_type bundle, output dir: $output_dir"
pushd "$output_dir"
    rpms_dir="${build_dir}/rpmbuild/RPMS/noarch/"

    if [[ "$output_type" == "deploy-cortx" ]]; then
        cp -r "${rpms_dir}"/* .
        yum_repos=(".")
        cortx_dir="."
    else
        yum_repos=("cortx_iso" "3rd_party")

        if [[ "$output_type" == "upgrade" ]]; then
            yum_repos+=("os")
        elif [[ -n "$orig_iso" ]]; then
            orig_bundle="$build_dir/orig_bundle"
            mkdir -p "$orig_bundle"
            echo -e "Mounting orginal ISO $orig_iso into $orig_bundle"
            mount -o loop "$orig_iso" "$orig_bundle"
        else
            yum_repos+=("3rd_party/EPEL-7" "3rd_party/commons/glusterfs" "3rd_party/commons/saltstack")
        fi

        mkdir -p python_deps "${yum_repos[@]}"
        cp -r "${rpms_dir}"/* cortx_iso
        cortx_dir="cortx_iso"
    fi

    # we create repos before copying existent ones inside it (if any)
    for repo in "${yum_repos[@]}"; do
        createrepo "$repo"
    done

    # copying existent repos inside
    if [[ -d "$orig_bundle" ]]; then
        pushd 3rd_party
            orig_repos=("EPEL-7" "commons/glusterfs" "commons/saltstack")
            mkdir commons
            for repo in "${orig_repos[@]}"; do
                cp -r "$orig_bundle/3rd_party/$repo" "$repo"
            done
        popd

        pushd "$cortx_dir"
            cp -f "$orig_bundle"/cortx_iso/*cortx-prvsnr*.rpm .
        popd
    fi

    # pack provided provisioner packages (if any) inside bundle
    pushd "$cortx_dir"
        if [[ -f "$prvsnr_pkg" ]]; then
            rm -f cortx-prvsnr*.rpm
            cp -f "$prvsnr_pkg" .
        fi

        if [[ -f "$prvsnr_api_pkg" ]]; then
            rm -f python36-cortx-prvsnr*.rpm
            cp -f "$prvsnr_api_pkg" .
        fi
    popd

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
