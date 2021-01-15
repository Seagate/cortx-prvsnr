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

LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/update-post-reboot.log}"
if [[ ! -e "$LOG_FILE" ]]; then
    mkdir -p $(dirname "${LOG_FILE}")
    touch "${LOG_FILE}"
fi

function trap_handler {
    echo -e "\n***** FAILED!!*****" 2>&1 | tee -a "$LOG_FILE"
    echo "Detailed error log is kept at: $LOG_FILE" 2>&1 | tee -a "$LOG_FILE"
    exit 1
}
trap trap_handler ERR

function post_boot_operations() {

    post_boot_op=$(salt-call pillar.get update_states:post_boot --output=newline_values_only)
    if [[ ${post_boot_op} ]]; then
        for state in ${post_boot_op}; do
            echo "Performing ${state} on target nodes" 2>&1 | tee -a "${LOG_FILE}"
            provisioner "${state}"
        done 
        provisioner pillar_set update_states/post_boot PRVSNR_UNDEFINED
    else
        echo "No operations to perform !!" 2>&1 | tee -a "${LOG_FILE}"
    fi
}

function usage {
  echo "\
Usage: $0

Perform provisioner operations after reboot.
"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) usage; exit 0
        ;;
        *) echo "Invalid option $1"; usage; exit 1;;
    esac
done

post_boot_operations

echo "***** SUCCESS! *****" 2>&1 | tee -a "${LOG_FILE}"
echo "The detailed logs can be seen at: $LOG_FILE" 2>&1 | tee -a "${LOG_FILE}"
echo "Done" 2>&1 | tee -a "${LOG_FILE}"
