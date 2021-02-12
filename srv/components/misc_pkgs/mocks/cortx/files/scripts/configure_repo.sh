#!/bin/bash

MOCK_REPO_DIR="/opt/seagate/cortx/provisioner/srv/components/misc_pkgs/mocks/cortx/files/cortx_mock_repo"
BUILD_DIR=$(realpath ~)

if [ ! -w "$MOCK_REPO_DIR" ]
then
    echo "No write permissions for ${MOCK_REPO_DIR}. Please, change user or use sudo."
    exit 1
fi

cp -r ${BUILD_DIR}/rpmbuild/RPMS/noarch/* ${MOCK_REPO_DIR}

createrepo ${MOCK_REPO_DIR}
