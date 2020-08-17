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

{% set node = grains['id'] %}
{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.build_ssl_cert_rpms'.format(grains['id'])) %}
{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(node), false) %}

include:
  - components.misc_pkgs.build_ssl_cert_rpms.install
  - components.misc_pkgs.build_ssl_cert_rpms.prepare
  - components.misc_pkgs.build_ssl_cert_rpms.config
  - components.misc_pkgs.build_ssl_cert_rpms.housekeeping
  - components.misc_pkgs.build_ssl_cert_rpms.sanity_check

# Copy generated cert from Master
{%- for node_id in pillar['cluster']['node_list'] -%}
{%- if not pillar['cluster'][node_id]['is_primary'] %}
# Requries pip install scp
# Copy certs to non-primary:
#   module.run:
#     - scp.put:
#       - files:
#         - /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm
#         - /opt/seagate/stx-s3-certs-1.0-1_s3dev.x86_64.rpm
#       - remote_path: /opt/seagate
#       - recursive: True
#       - preserve_times: True
#       - hostname: pillar['cluster'][node_id]['hostname']
#       - auto_add_policy: True

Copy certs to non-primary:
  cmd.run:
    - name: scp /opt/seagate/stx-s3-*.rpm {{ pillar['cluster'][node_id]['hostname'] }}:/opt/seagate/

{%- endif -%}
{%- endfor -%}
{%- else -%}
build_cert_rpms_non_primary_node:
  test.show_notification:
    - text: "No changes needed on non-primary node: {{ node }}"
{% endif %}

Generate openldap checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.build_ssl_cert_rpms
    - makedirs: True
    - create: True
{%- else -%}
SSL cert rpms built already:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.build_ssl_cert_rpms.teardown' to reprovision these states."
{% endif %}
