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

include:
  - components.misc_pkgs.consul.prepare
  - components.misc_pkgs.consul.install

Set consul in bash_profile:
  file.blockreplace:
    - name: ~/.bashrc
    - marker_start: '# DO NOT EDIT: Consul binaries'
    - marker_end: '# DO NOT EDIT: End'
    - content: 'export PATH=/opt/consul:$PATH'
    - append_if_not_found: True
    - append_newline: True
    - backup: False
    - require:
      - Consul installed

Source bash_profile for nodejs addition:
  cmd.run:
    - name: source ~/.bashrc
    - require:
      - Set consul in bash_profile

Reload service daemons for consul-agent.service:
  cmd.run:
    - name: systemctl daemon-reload
    - require:
      - file: Create Consul Agent Service
      - Consul installed
