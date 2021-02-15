#!/bin/bash

set -eu

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

VERSION="${1:-2.0.0}"
BUILD_DIR="${2:-(realpath ~)}"
SPEC=cortx-mock.spec
SPEC_NO_API=cortx-mock-no-api.spec

WORKING_DIR="$(realpath $script_dir/..)"

PKG_COMP_LIST=(
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
)

rm -rf "${BUILD_DIR}"/rpmbuild
mkdir -p "${BUILD_DIR}"/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

pushd ${BUILD_DIR}
    cp ${WORKING_DIR}/specs/cortx-mock.spec "rpmbuild/SPECS/${SPEC}"
    grep -v setup.yaml ${WORKING_DIR}/specs/cortx-mock.spec >"rpmbuild/SPECS/${SPEC_NO_API}"

    pushd rpmbuild
        for comp_pkg in ${PKG_COMP_LIST[@]}; do
            IFS=',' read -r -a array <<< "$comp_pkg"
            pkg="${array[0]}"
            comp="${array[1]:-}"
            pkg_dir="${pkg}-${VERSION}"
            spec="$SPEC_NO_API"
            comp_define=

            echo -e "Building package $pkg"
            mkdir -p "./SOURCES/${pkg_dir}"

            if [[ -n "$comp" ]]; then
                sed "s/{{ component }}/$comp/g" ${WORKING_DIR}/setup.yaml >SOURCES/${pkg_dir}/setup.yaml
                spec="$SPEC"
            fi

            tar czf "SOURCES/${pkg_dir}.tar.gz" -C SOURCES "${pkg_dir}"
            rpmbuild -ba --define "_topdir ${BUILD_DIR}/rpmbuild" \
                            --define "__NAME__ ${pkg}" \
                            --define "__VERSION__ ${VERSION}" \
                            --define "__COMPONENT__ $comp" \
                            "SPECS/${spec}"
        done
    popd
popd
