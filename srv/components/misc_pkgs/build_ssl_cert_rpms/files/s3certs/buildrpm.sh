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


# Note: This is currently interactive script since following script is
#  interactive: <s3 src>/scripts/ssl/generate_certificate.sh

set -e

SCRIPT_PATH=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT_PATH")

DEPLOY_TAG=
# We use s3 server version for cert package versioning so to know certs package
# was created for which version of S3.
S3_VERSION=1.0.0
S3_DOMAIN=s3.seagate.com

usage() { echo "Usage: $0 -T <short deployment tag> [-S <S3 version>]
                [-D s3_domain] [-h Show help]" 1>&2; exit 1; }

while getopts ":D:T:S:h" o; do
    case "${o}" in
        T)
            DEPLOY_TAG=${OPTARG}
            ;;
        S)
            S3_VERSION=s3ver${OPTARG}
            ;;
        D)
            S3_DOMAIN=${OPTARG}
            ;;
        h)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${DEPLOY_TAG}" ]; then
    echo "Missing -T option."
    usage
fi

echo "Using [S3_VERSION=${S3_VERSION}] ..."
echo "Using [DEPLOY_TAG=${DEPLOY_TAG}] ..."
echo "Using [S3_DOMAIN=${S3_DOMAIN}] ..."

mkdir -p ~/rpmbuild/SOURCES/
cd ~/rpmbuild/SOURCES/
rm -rf stx-s3-certs*

# Setup the source tar for rpm build
S3_CERTS_SRC=stx-s3-certs-${S3_VERSION}-${DEPLOY_TAG}

mkdir ${S3_CERTS_SRC}
cd ${S3_CERTS_SRC}

# Generate the certificates
${BASEDIR}/ssl/generate_certificate.sh
cp -r ./s3_certs_sandbox/* .
rm -rf ./s3_certs_sandbox

cd ~/rpmbuild/SOURCES/

tar -zcvf ${S3_CERTS_SRC}.tar.gz ${S3_CERTS_SRC}
rm -rf ${S3_CERTS_SRC}

rpmbuild -ba --define "_s3_certs_version ${S3_VERSION}"  \
         --define "_s3_certs_src ${S3_CERTS_SRC}"  \
         --define "_s3_domain_tag ${S3_DOMAIN}"  \
         --define "_s3_deploy_tag ${DEPLOY_TAG}" ${BASEDIR}/s3certs.spec

rpmbuild -ba --define "_s3_certs_version ${S3_VERSION}"  \
         --define "_s3_certs_src ${S3_CERTS_SRC}"  \
         --define "_s3_domain_tag ${S3_DOMAIN}"  \
         --define "_s3_deploy_tag ${DEPLOY_TAG}" ${BASEDIR}/s3clientcerts.spec
