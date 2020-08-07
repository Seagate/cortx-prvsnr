#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

#!/bin/sh

set -e

SCRIPT_PATH=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT_PATH")

BUILD_NUMBER=0
GIT_VER=
CORTX_PRVSNR_VERSION=1.0.0

usage() { echo "Usage: $0 [-G <git short revision>] [-S <CORTX Provisioner version>]" 1>&2; exit 1; }

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
            echo "Usage: buildrpm.sh -g <git_commit_hash> -e <ees_prvsnr_version> -b <build_number>"
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

    rm -rf cortx-prvsnr*

    # Setup the source tar for rpm build
    DEST_DIR=cortx-prvsnr-${CORTX_PRVSNR_VERSION}-git${GIT_VER}
    mkdir -p ${DEST_DIR}/{cli,files/etc,files/conf,pillar,srv,api}
    cp -R ${BASEDIR}/../../cli/src/* ${DEST_DIR}/cli
    cp -R ${BASEDIR}/../../srv/components/provisioner/files/setup.yaml ${DEST_DIR}/files/conf
    cp -R ${BASEDIR}/../../pillar ${DEST_DIR}
    cp -R ${BASEDIR}/../../srv ${DEST_DIR}
    cp -R ${BASEDIR}/../../api ${DEST_DIR}


    tar -zcvf ${DEST_DIR}.tar.gz ${DEST_DIR}
    rm -rf ${DEST_DIR}

    yum-builddep -y ${BASEDIR}/cortx-prvsnr.spec

    rpmbuild -bb --define "_cortx_prvsnr_version ${CORTX_PRVSNR_VERSION}" --define "_cortx_prvsnr_git_ver git${GIT_VER}" --define "_build_number ${BUILD_NUMBER}" ${BASEDIR}/cortx-prvsnr.spec

popd

# Remove rpm-build package
#[[ $(rpm --quiet -qi rpm-build) == 0 ]] && yum remove -q -y rpm-build
