#!/bin/bash
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


set -eux

NO_CLEANUP="${NO_CLEANUP:-}"

grep -q -i -e 'rhel\|centos' /etc/*-release && {
    echo "RedHat"

    yum remove -y \
        docker \
        docker-client \
        docker-client-latest \
        docker-common \
        docker-latest \
        docker-latest-logrotate \
        docker-logrotate \
        docker-engine

    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

    yum install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io

    if [[ -z "$NO_CLEANUP" ]]; then
        rm -rf /var/cache/yum
    fi

    exit 0
}


grep -q -i -e 'ubuntu' /etc/*-release && {
    apt-get update -y

    apt-get remove -y \
            docker \
            docker-engine \
            docker.io \
            containerd \
            runc \
        || true

    apt-get -y \
        install \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --batch --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io

    if [[ -z "$NO_CLEANUP" ]]; then
        rm -rf /var/lib/apt/lists/*
    fi

    exit 0
}




grep -q -i -e 'debian' /etc/*-release && {
    apt-get update -y

    apt-get remove -y \
            docker \
            docker-engine \
            docker.io \
            containerd \
            runc \
        || true

    apt-get -y \
        install \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --batch --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io

    if [[ -z "$NO_CLEANUP" ]]; then
        rm -rf /var/lib/apt/lists/*
    fi

    exit 0
}

>&2 echo -e "$0: Not implemented - unexpected system release data in \
    $(ls /etc/*-release):\n$(cat /etc/*-release)"

exit 1
