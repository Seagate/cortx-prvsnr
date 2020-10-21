#!/bin/sh
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

SCRIPT_PATH=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT_PATH")

BUILD_NUMBER=0
GIT_VER=
CORTX_PRVSNR_VERSION=1.0.0

#usage() { echo "Usage: $0 [-G <git short revision>] [-P <CORTX Provisioner version>]" 1>&2; exit 1; }

# Install rpm-build package
rpm --quiet -qi git || yum install -q -y git && echo "git already installed."
rpm --quiet -qi python3-3.6.* || yum install -q -y python36 && echo "python36 already installed."
rpm --quiet -qi rpm-build || yum install -q -y rpm-build && echo "rpm-build already installed."
rpm --quiet -qi yum-utils || yum install -q -y yum-utils && echo "yum-utils already installed."

# Clean-up pycache
find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +

while getopts ":g:e:b:" o; do
    case "${o}" in
        g)
            GIT_VER=${OPTARG}
            ;;
        e)
            CORTX_PRVSNR_VERSION=${OPTARG}
            ;;
        b)
            BUILD_NUMBER=${OPTARG}
            ;;
        *)
            echo "Usage: buildrpm.sh -g <git_commit_hash> -e <cortx_prvsnr_version> -b <build_number>"
            exit 0
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${GIT_VER}" ]; then
    GIT_VER=`git rev-parse --short HEAD`
fi

echo "Using [CORTX_PRVSNR_VERSION=${CORTX_PRVSNR_VERSION}] ..."
echo "Using [GIT_VER=${GIT_VER}] ..."

mkdir -p ~/rpmbuild/SOURCES/
pushd ~/rpmbuild/SOURCES/


    rm -rf cortx-prvsnr-cli*

    DEST_DIR=cortx-prvsnr-cli-${CORTX_PRVSNR_VERSION}-git${GIT_VER}
    # Setup the source tar for rpm build
    mkdir -p ${DEST_DIR}/{cli,files/etc,files/.ssh}
    cp -pr ${BASEDIR}/src ${DEST_DIR}/cli
    cp -pr ${BASEDIR}/../files/etc/yum.repos.d ${DEST_DIR}/files/etc

    tar -czvf ${DEST_DIR}.tar.gz ${DEST_DIR}
    rm -rf cortx-prvsnr-cli-${CORTX_PRVSNR_VERSION}-git${GIT_VER}

    yum-builddep -y ${BASEDIR}/cortx-prvsnr-cli.spec

    rpmbuild -bb --define "_cortx_prvsnr_version ${CORTX_PRVSNR_VERSION}" --define "_cortx_prvsnr_git_ver git${GIT_VER}" --define "_build_number ${BUILD_NUMBER}" ${BASEDIR}/cortx-prvsnr-cli.spec

popd

# Remove rpm-build package
#[[ $(rpm --quiet -qi rpm-build) == 0 ]] && yum remove -q -y rpm-build
