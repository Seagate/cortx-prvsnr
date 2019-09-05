#!/bin/sh

set -e

SCRIPT_PATH=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT_PATH")

GIT_VER=
EOS_PRVSNR_VERSION=1.0.0

usage() { echo "Usage: $0 [-G <git short revision>] [-S <EOS Provisioner version>]" 1>&2; exit 1; }

# Install rpm-build package
[[ $(rpm --quiet -qi rpm-build) != 0 ]] && yum install -q -y rpm-build

# Clean-up pycache
find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +

while getopts ":G:S:" o; do
    case "${o}" in
        G)
            GIT_VER=${OPTARG}
            ;;
        S)
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
pushd ~/rpmbuild/SOURCES/
rm -rf eos-prvsnr*

# Setup the source tar for rpm build
mkdir -p eos-prvsnr-${EOS_PRVSNR_VERSION}-git${GIT_VER}
cp -R ${BASEDIR}/../files eos-prvsnr-${EOS_PRVSNR_VERSION}-git${GIT_VER}/
cp -R ${BASEDIR}/../pillar eos-prvsnr-${EOS_PRVSNR_VERSION}-git${GIT_VER}/
cp -R ${BASEDIR}/../srv eos-prvsnr-${EOS_PRVSNR_VERSION}-git${GIT_VER}/
cp -R ${BASEDIR}/../utils eos-prvsnr-${EOS_PRVSNR_VERSION}-git${GIT_VER}/

tar -zcvf eos-prvsnr-${EOS_PRVSNR_VERSION}-git${GIT_VER}.tar.gz eos-prvsnr-${EOS_PRVSNR_VERSION}-git${GIT_VER}
rm -rf eos-prvsnr-${EOS_PRVSNR_VERSION}-git${GIT_VER}

sudo yum-builddep -y ${BASEDIR}/eos-prvsnr.spec

rpmbuild -bb --define "_ees_prvsnr_version ${EOS_PRVSNR_VERSION}" --define "_ees_prvsnr_git_ver git${GIT_VER}" ${BASEDIR}/eos-prvsnr.spec

popd

# Remove rpm-build package
#[[ $(rpm --quiet -qi rpm-build) == 0 ]] && yum remove -q -y rpm-build
