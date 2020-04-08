#!/bin/sh

set -eu

SCRIPT_PATH=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT_PATH")

BUILD_NUMBER=0
GIT_VER=
EOS_PRVSNR_VERSION=1.0.0

#usage() { echo "Usage: $0 [-G <git short revision>] [-P <EOS Provisioner version>]" 1>&2; exit 1; }

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
            EOS_PRVSNR_VERSION=${OPTARG}
            ;;
        b)
            BUILD_NUMBER=${OPTARG}
            ;;
        *)
            echo "Usage: buildrpm.sh -g <git_commit_hash> -e <ees_prvsnr_version> -b <build_number>"
            exit 0
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${GIT_VER}" ]; then
    GIT_VER=`git rev-parse --short HEAD`
fi

echo "Using [EOS_PRVSNR_VERSION=${EOS_PRVSNR_VERSION}] ..."
echo "Using [GIT_VER=${GIT_VER}] ..."

mkdir -p ~/rpmbuild/SOURCES/
pushd ~/rpmbuild/SOURCES/

    rm -rf eos-prvsnr-cli*

    DEST_DIR=eos-prvsnr-cli-${EOS_PRVSNR_VERSION}-git${GIT_VER}
    # Setup the source tar for rpm build
    mkdir -p ${DEST_DIR}/cli
    mkdir -p ${DEST_DIR}/files/etc/salt
    mkdir -p ${DEST_DIR}/files/etc/sysconfig/network-scripts
    mkdir -p ${DEST_DIR}/files/etc/modprobe.d/
    mkdir -p ${DEST_DIR}/files/etc/yum.repos.d/
    mkdir -p ${DEST_DIR}/files/conf/
    mkdir -p ${DEST_DIR}/files/.ssh/
    mkdir -p ${DEST_DIR}/files/syslogconfig/
    cp -pr ${BASEDIR}/src/* ${DEST_DIR}/cli
    cp -pr ${BASEDIR}/utils ${DEST_DIR}/cli
    cp -pr ${BASEDIR}/../files/etc/salt/* ${DEST_DIR}/files/etc/salt
    # cp -pr ${BASEDIR}/../files/etc/sysconfig/network-scripts/ifcfg-* ${DEST_DIR}/files/etc/sysconfig/network-scripts/
    cp -p ${BASEDIR}/../files/etc/modprobe.d/bonding.conf ${DEST_DIR}/files/etc/modprobe.d/bonding.conf
    cp -pr ${BASEDIR}/../files/etc/yum.repos.d/* ${DEST_DIR}/files/etc/yum.repos.d/
    cp -pr ${BASEDIR}/../files/.ssh/* ${DEST_DIR}/files/.ssh/
    cp -pr ${BASEDIR}/../files/syslogconfig/* ${DEST_DIR}/files/syslogconfig/
    cp -pr ${BASEDIR}/../files/conf/* ${DEST_DIR}/files/conf/

    tar -czvf ${DEST_DIR}.tar.gz ${DEST_DIR}
    rm -rf eos-prvsnr-cli-${EOS_PRVSNR_VERSION}-git${GIT_VER}

    yum-builddep -y ${BASEDIR}/eos-prvsnr-cli.spec

    rpmbuild -bb --define "_ees_prvsnr_version ${EOS_PRVSNR_VERSION}" --define "_ees_prvsnr_git_ver git${GIT_VER}" --define "_build_number ${BUILD_NUMBER}" ${BASEDIR}/eos-prvsnr-cli.spec

popd

# Remove rpm-build package
#[[ $(rpm --quiet -qi rpm-build) == 0 ]] && yum remove -q -y rpm-build
