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

{% if pillar['cluster'][grains['id']]['is_primary'] -%}
{%- if pillar['cluster']['mgmt_vip'] %}
Update Management VIP:
  cmd.run:
    - name: pcs resource update kibana-vip ip={{ pillar['cluster']['mgmt_vip'] }}
{% else %}
Missing Management VIP:
  test.fail_without_changes:
    - name: Management VIP is blank in Cluster.sls. Please udpate with valid IP and re-run.
{% endif %}
{% else %}
No Management VIP application:
  test.show_notification:
    - text: "Management VIP application only applies to primary node. There's no execution on secondary node"
{% endif %}
