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

{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.openldap_replication'.format(grains['id'])) %}
include:
  - components.misc_pkgs.openldap.replication.prepare
  - components.misc_pkgs.openldap.replication.config
  - components.misc_pkgs.openldap.replication.sanity_check

Generate openldap replication checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.openldap_replication
    - makedirs: True
    - create: True
{%- else -%}
OpenLDAP replication already applied:
  test.show_notification:
    - text: "OpenLDAP replication states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.openldap.teardown' to reprovision these states."
{% endif %}
