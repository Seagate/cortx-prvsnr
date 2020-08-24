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
  - components.ha.iostack-ha.prepare
  - components.ha.cortx-ha.prepare
  - components.ha.cortx-ha.install

Copy file setup-ees.yaml:
  file.copy:
    - name: /opt/seagate/cortx/iostack-ha/conf/setup.yaml
    - source: /opt/seagate/cortx/ha/conf/setup-ees.yaml
    - force: False      # Failsafe once cortx-ha fixes the path
    - makedirs: True
    - preserve: True

Rename root node to iostack-ha:
  file.replace:
    - name: /opt/seagate/cortx/iostack-ha/conf/setup.yaml
    - pattern: "ees-ha:"
    - repl: "iostack-ha:"
    - count: 1
  