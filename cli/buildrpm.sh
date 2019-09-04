#!/bin/sh

set -e

SCRIPT_PATH=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT_PATH")

GIT_VER=
EOS_PRVSNR_VERSION=1.0.0

usage() { echo "Usage: $0 [-G <git short revision>] [-P <EOS Provisioner version>]" 1>&2; exit 1; }

[[ $(rpm --quiet -qi rpm-build) != 0 ]] && yum install -q -y rpm-build

while getopts ":G:S:" o; do
    case "${o}" in
        G)
            GIT_VER=${OPTARG}
            ;;
        P)
            EOS_PRVSNR_VERSION=${OPTARG}
            ;;
        *)
            usage
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
cd ~/rpmbuild/SOURCES/
rm -rf eos-prvsnr-cli*

# Setup the source tar for rpm build
mkdir -p eos-prvsnr-cli-${EOS_PRVSNR_VERSION}-git${GIT_VER}
cp -R ${BASEDIR}/ eos-prvsnr-cli-${EOS_PRVSNR_VERSION}-git${GIT_VER}/cli
tar -czvf eos-prvsnr-cli-${EOS_PRVSNR_VERSION}-git${GIT_VER}.tar.gz eos-prvsnr-cli-${EOS_PRVSNR_VERSION}-git${GIT_VER}
rm -rf eos-prvsnr-cli-${EOS_PRVSNR_VERSION}-git${GIT_VER}

rpmbuild -bb --define "_ees_prvsnr_version ${EOS_PRVSNR_VERSION}"  --define "_ees_prvsnr_git_ver git${GIT_VER}" ${BASEDIR}/eos-prvsnr-cli.spec

#[[ $(rpm --quiet -qi rpm-build) == 0 ]] && yum remove -q -y rpm-build
