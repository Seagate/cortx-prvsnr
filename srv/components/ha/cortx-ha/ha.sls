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

{% if pillar['cluster'][grains['id']]['is_primary'] %}
include:
  - components.ha.cortx-ha.install
  - components.ha.ees_ha.prepare

Run cortx-ha HA setup:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/ha/conf/setup.yaml', 'ha:ha')
    - require:
      - Install cortx-ha
      - Render ha input params template
{% else %}
No HA setup on secondary node:
  test.show_notification:
    - text: "HA setup applies to primary node. There's no execution on secondary node"
{% endif %}
