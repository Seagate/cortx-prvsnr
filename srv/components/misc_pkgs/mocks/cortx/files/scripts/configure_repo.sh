#!/bin/bash

if [ "$1" != "" ]; then
    BUILD_DIR=$1
else
   echo "Path to dir with rpmbuild directory which contains rpm artifacts is missed. Usage: ${0} <Path to dir with rpmbuild>"
   echo "Oridinary, it is the users home dir, e.g.: /home/<your UGID>/"
   exit 1
fi

MOCK_REPO_DIR="/opt/seagate/cortx/provisioner/srv/components/misc_pkgs/mocks/cortx/files/cortx_mock_repo"

if [ ! -w "$MOCK_REPO_DIR" ]
then
    echo "No write permissions for ${MOCK_REPO_DIR}. Please, change user or use sudo."
    exit 1
fi

cp -r ${BUILD_DIR}/rpmbuild/RPMS/noarch/* ${MOCK_REPO_DIR}

createrepo ${MOCK_REPO_DIR}
