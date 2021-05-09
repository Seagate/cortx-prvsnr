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

{% set node = grains['id'] %}
{% if not salt['file.file_exists']('/opt/seagate/cortx_configs/provisioner_generated/{0}.build_ssl_cert_rpms'.format(grains['id'])) %}
{% if "primary" in pillar["cluster"][grains["id"]]["roles"] %}

include:
  - misc_pkgs.build_ssl_cert_rpms.install
  - misc_pkgs.build_ssl_cert_rpms.prepare
  - misc_pkgs.build_ssl_cert_rpms.config
  - misc_pkgs.build_ssl_cert_rpms.housekeeping
  - misc_pkgs.build_ssl_cert_rpms.sanity_check

# Copy generated cert from primary server node
{% set server_nodes = [ ] %}
{% for node in pillar['cluster'].keys() -%}
{% if "srvnode-" in node -%}
{% do server_nodes.append(node)-%}
{% endif -%}
{% endfor -%}
{%- for node_id in server_nodes -%}
{%- if not "primary" in pillar['cluster'][node_id]['roles'] %}
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
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.build_ssl_cert_rpms
    - makedirs: True
    - create: True
{%- else -%}
SSL cert rpms built already:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply misc_pkgs.build_ssl_cert_rpms.teardown' to reprovision these states."
{% endif %}
