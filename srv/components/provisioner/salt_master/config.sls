#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

salt_master_config_updated:
  file.managed:
    - name: /etc/salt/master
    - source: salt://components/provisioner/salt_master/files/master


salt_master_service_enabled:
  service.enabled:
    - name: salt-master
    - require:
      - file: salt_master_config_updated


# Note. master restart is in foreground,
# so minion will reported to restarted master
salt_master_service_restarted:
  cmd.run:
    # 1. test.true will prevent restart of salt master if the config is malformed
    # 2. --local is required if salt-master is actually not running,
    #    since state might be called by salt-run as well
    - name: 'salt-run salt.cmd test.true && salt-call --local service.restart salt-master'
    - bg: True
    - onchanges:
      - file: salt_master_config_updated
