#!/bin/bash

set -eu

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

VERSION="${1:-2.0.0}"
BUILD="${2:-1}"
BUILD_DIR="${3:-(realpath ~)}"
SPEC=cortx-mock.spec
SPEC_NO_API=cortx-mock-no-api.spec

WORKING_DIR="$(realpath "$script_dir/..")"

# TODO a kind of duplication for pillar/components/commons.sls
# TODO provisioner pkgs
PKG_COMP_LIST=(
    "cortx-py-utils,utils"
    "cortx-csm_agent,csm"
    "cortx-hare,hare"
    "cortx-motr,motr"
    "cortx-s3server,s3"
    "cortx-ha,ha"
    "cortx-sspl,sspl"
    "uds-pyi,uds"
    "cortx-cli,"
    "cortx-sspl-test,"
    "cortx-s3iamcli,"
    "cortx-csm_web,"
    "cortx-prvsnr,provisioner"
    "python36-cortx-prvsnr,"
)

rm -rf "${BUILD_DIR}"/rpmbuild
mkdir -p "${BUILD_DIR}"/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

mock_spec="${WORKING_DIR}/specs/cortx-mock.spec"
mock_setup_yaml="${WORKING_DIR}/setup.yaml"

pushd "${BUILD_DIR}"
    cp "$mock_spec" "rpmbuild/SPECS/${SPEC}"
    # not all packages come with setup.yaml (provisioner mini API) since:
    # - a CORTX component may have multiple pkgs
    # - but only one of them setups the API
    grep -v setup.yaml "$mock_spec" >"rpmbuild/SPECS/${SPEC_NO_API}"

    pushd rpmbuild
        for comp_pkg in "${PKG_COMP_LIST[@]}"; do
            IFS=',' read -r -a array <<< "$comp_pkg"
            pkg="${array[0]}"
            comp="${array[1]:-}"
            pkg_dir="${pkg}-${VERSION}"
            spec="$SPEC_NO_API"

            echo -e "Building package $pkg"
            mkdir -p "./SOURCES/${pkg_dir}"

            defines=(
               "--define" "_topdir ${BUILD_DIR}/rpmbuild"
               "--define" "__NAME__ ${pkg}"
               "--define" "__VERSION__ ${VERSION}"
               "--define" "__BUILD__ ${BUILD}"
            )

            if [[ -n "$comp" ]]; then
                sed "s/{{ component }}/$comp/g" "$mock_setup_yaml" >"SOURCES/${pkg_dir}/setup.yaml"
                spec="$SPEC"
                defines+=("--define" "__COMPONENT__ $comp")
            fi

            tar czf "SOURCES/${pkg_dir}.tar.gz" -C SOURCES "${pkg_dir}"
            rpmbuild --quiet -ba "${defines[@]}" "SPECS/${spec}"
        done
    popd
popd
