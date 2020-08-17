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

salt_minion_config_updated:
  file.managed:
    - name: /etc/salt/minion
    - source: salt://components/provisioner/salt_minion/files/minion
    - template: jinja


salt_minion_service_enabled:
  service.enabled:
    - name: salt-minion
    - require:
      - file: salt_minion_config_updated


salt_minion_service_restarted:
  cmd.run:
    - name: 'salt-call service.restart salt-minion'
    - bg: True
    - onchanges:
      - file: salt_minion_config_updated
