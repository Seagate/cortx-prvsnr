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

set -euE

LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/cortx_prep.log}"
if [[ ! -e "$LOG_FILE" ]]; then
    mkdir -p $(dirname "${LOG_FILE}")
    touch "${LOG_FILE}"
fi

function trap_handler {
    echo -e "\n***** FAILED!!*****" 2>&1 | tee -a $LOG_FILE
    echo "Detailed error log is kept at: $LOG_FILE" 2>&1 | tee -a $LOG_FILE
    exit 1
}
trap trap_handler ERR

function install_prvsnr() {

    echo "INFO: Creating a directory to serve as the mount point" 2>&1 | tee -a ${LOG_FILE}
    mkdir -p /tmp/iso_mount/{cortx,cortx-os}

    if [[ `find /opt/isos -name '*.iso'` ]]; then
        cortx_iso=$(ls -t /opt/isos/cortx-*-single.iso 2> /dev/null | head -1 | xargs basename)
        os_iso=$(ls -t /opt/isos/cortx-os-*.iso 2> /dev/null | head -1 | xargs basename)

        echo "INFO: Mounting ${cortx_iso} ${os_iso} on /tmp/iso_mount directory" 2>&1 | tee -a ${LOG_FILE}
        mount -t iso9660 /opt/isos/${cortx_iso} /tmp/iso_mount/cortx 2>&1 | tee -a ${LOG_FILE}
        mount -t iso9660 /opt/isos/${os_iso} /tmp/iso_mount/cortx-os 2>&1 | tee -a ${LOG_FILE}

        echo "INFO: Backing up exisitng repositories" 2>&1 | tee -a "${LOG_FILE}"
        mv /etc/yum.repos.d /etc/yum.repos.d.bak

        echo "INFO: Creating bootstrap.repo" 2>&1 | tee -a ${LOG_FILE}
        mkdir -p /etc/yum.repos.d && touch /etc/yum.repos.d/bootstrap.repo
        for repo in 3rd_party cortx_iso
        do
cat >> /etc/yum.repos.d/bootstrap.repo <<EOF
[$repo]
baseurl=file:///tmp/iso_mount/cortx/${repo}
gpgcheck=0
name=Repository ${repo}
enabled=1

EOF
      done

        echo "INFO: Creating base.repo" 2>&1 | tee -a ${LOG_FILE}
        touch /etc/yum.repos.d/base.repo
cat >> /etc/yum.repos.d/base.repo <<EOF
[Base]
baseurl=file:///tmp/iso_mount/cortx-os
gpgcheck=0
name=Repository Base
enabled=1
EOF
        echo "INFO: Installing cortx-prvsnr packages" 2>&1 | tee -a ${LOG_FILE}
        yum clean all || true
        yum install -y \
        python3 python36-m2crypto \
        salt-api salt-master salt-minion \
        python36-cortx-prvsnr \
        sshpass \
        2>&1 | tee -a ${LOG_FILE}

        echo "INFO: Verifying cortx-prvsnr installation" 2>&1 | tee -a ${LOG_FILE}
        prvsnr_version=$(provisioner --version)
        if [[ $?==0 ]]; then
          echo "INFO: Successfully installed cortx-prvsnr!!" 2>&1 | tee -a ${LOG_FILE}
        else
          echo "ERROR: cortx-prvsnr not installed" 2>&1 | tee -a ${LOG_FILE}
          exit 1
        fi

        echo "INFO: Removing bootstrap and base repo files" 2>&1 | tee -a ${LOG_FILE}
        rm -f /etc/yum.repos.d/bootstrap.repo && rm -f /etc/yum.repos.d/base.repo
        yum clean all || true

        echo "INFO: Unmounting ${cortx_iso} ${os_iso} from /tmp/iso_mount" 2>&1 | tee -a ${LOG_FILE}
        umount /tmp/iso_mount/cortx 2>&1 | tee -a ${LOG_FILE}
        umount /tmp/iso_mount/cortx-os 2>&1 | tee -a ${LOG_FILE}

        echo "Done." 2>&1 | tee -a ${LOG_FILE}
    else
        echo "ERROR: OS and CORTX ISO not found at /opt/isos/" 2>&1 | tee -a ${LOG_FILE}
        exit 1
    fi
}

function usage {
  echo "\
Usage: $0

Installs cortx-prvsnr API (python36-cortx-prvsnr)

Must preferably be run from primary node.
"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) usage; exit 0
        ;;
        *) echo "Invalid option $1"; usage; exit 1;;
    esac
done

install_prvsnr

echo "***** SUCCESS! *****" 2>&1 | tee -a ${LOG_FILE}
echo "The detailed logs can be seen at: $LOG_FILE" 2>&1 | tee -a ${LOG_FILE}
echo "Done" 2>&1 | tee -a ${LOG_FILE}
