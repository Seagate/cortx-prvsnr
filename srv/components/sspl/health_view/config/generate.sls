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
  - components.sspl.install
  - components.sspl.config.commons

{% set enclosure = '' %}
{% if "primary" in grains["roles"] and 'physical' in grains['virtual'] %}
# run health schema on master for both node and enclosure; on minion only for node health.
{% set enclosure = '-e' %}
{% endif %}
Run Resource Health View:
  cmd.run:
    - name: /opt/seagate/cortx/sspl/lib/resource_health_view -n {{ enclosure }} --path /tmp
    - require:
      - Install cortx-sspl packages
      - Add common config - system information to Consul
      - Add common config - rabbitmq cluster to Consul
      - Add common config - BMC to Consul
      - Add common config - storage enclosure to Consul
