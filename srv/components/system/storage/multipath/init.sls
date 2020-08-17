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

{% if "physical" in grains['virtual'] %}
{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.multipath'.format(grains['id'])) %}
include:
  - components.system.storage.teardown.tidy-up
  - components.system.storage.multipath.prepare
  - components.system.storage.multipath.install
  - components.system.storage.multipath.config

Generate multipath checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.multipath
    - makedirs: True
    - create: True
{%- else -%}
multipath already applied:
  test.show_notification:
    - text: "multipath states already executed on node: {{ grains['id'] }}. execute 'salt '*' state.apply components.system.multipath.teardown' to reprovision these states."
{% endif %}
{%- else -%}
multipath wont be applied on VM:
  test.show_notification:
    - text: "multipath states wont be applied on VM node: {{ grains['id'] }}."

{% endif %}
