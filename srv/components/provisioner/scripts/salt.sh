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
#!/bin/bash

set -euE

PRVSNR_ROOT="/opt/seagate/cortx/provisioner"
minion_id="srvnode-0"
export LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/salt_local_config.log}"
mkdir -p $(dirname "${LOG_FILE}")


# 1. Point minion to local host master in /etc/salt/minion
# 2. Restart salt-minion service
# 3. Check if 'salt srvnode-0 test.ping' works

# TODO need to configure logging and route o/p to another file.

#echo "Starting provisioner environment configuration"
if ! rpm -qa | grep -iEwq "salt|salt-master|salt-minion|cortx-prvsnr"; then
    echo "ERROR: salt packages are not installed, please install salt packages and try again." >> "${LOG_FILE}"
    exit 1
fi

minion_file="${PRVSNR_ROOT}/srv/components/provisioner/salt_minion/files/minion_factory"
master_file="${PRVSNR_ROOT}/srv/components/provisioner/salt_master/files/master"

yes | cp -f "${master_file}" /etc/salt/master
yes | cp -f "${minion_file}" /etc/salt/minion

echo $minion_id > /etc/salt/minion_id

#echo "Restarting the required services"
systemctl start salt-master
systemctl restart salt-minion
sleep 10
status=$(systemctl status salt-minion | grep Active | awk '{ print $2 }')
if [[ "$status" != "active" ]]; then
    echo "Salt minion service failed to start" >> "${LOG_FILE}"
    echo "Could not start the required services to set up the environment" >> "${LOG_FILE}"
    exit 1
fi
echo "Done" >> "${LOG_FILE}"
echo "Verifying the configuraion" >> "${LOG_FILE}"
echo "DEBUG: Waiting for key of $minion_id to become connected to salt-master" >> "${LOG_FILE}"
try=1; max_tries=10
until salt-key --list-all | grep "srvnode-0" >/dev/null 2>&1
do
    if [[ "$try" -gt "$max_tries" ]]; then
        echo "ERROR: Key for salt-minion $minion_id not listed after $max_tries attemps." >> "${LOG_FILE}"
        echo "ERROR: Cortx provisioner environment configuration failed" >> "${LOG_FILE}"
        salt-key --list-all >&2
        exit 1
    fi
    try=$(( try + 1 ))
    sleep 5
done
echo "DEBUG: Key for $minion_id is listed." >> "${LOG_FILE}"
echo "DEBUG: Accepting the salt key for minion $minion_id" >> "${LOG_FILE}"
salt-key -y -a "$minion_id" --no-color --out-file="${LOG_FILE}" --out-file-append

# Check if salt '*' test.ping works
echo "Testing if the environment is working fine" >> "${LOG_FILE}"
try=1; max_tries=10
until salt -t 1 "$minion_id" test.ping >/dev/null 2>&1
do
    if [[ "$try" -gt "$max_tries" ]]; then
        echo "ERROR: Minion $minion_id seems still not ready after $max_tries attempts." >> "${LOG_FILE}"
        echo "ERROR: Cortx provisioner environment configuration failed" >> "${LOG_FILE}"
        exit 1
    fi
    try=$(( try + 1 ))
done
echo "DEBUG: Salt configuration done successfully" >> "${LOG_FILE}"

yes | cp -rf /opt/seagate/cortx/provisioner/backup_factory/hosts /etc/hosts
rm -rf /root/.ssh
systemctl restart salt-master
systemctl restart salt-minion
echo "Post-factory salt environment configured successfully" >> "${LOG_FILE}"
echo "Done" >> "${LOG_FILE}"
