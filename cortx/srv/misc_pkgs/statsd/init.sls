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

{% if not salt['file.file_exists']('/opt/seagate/cortx_configs/provisioner_generated/{0}.statsd'.format(grains['id'])) %}
include:
  - misc_pkgs.statsd.prepare
  - misc_pkgs.statsd.install
  - misc_pkgs.statsd.config
  - misc_pkgs.statsd.start
  - misc_pkgs.statsd.sanity_check

Generate statsd checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.statsd
    - makedirs: True
    - create: True

{%- else -%}

statsd already applied:
  test.show_notification:
    - text: "Statsd states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply statsd.teardown' to reprovision these states."

{%- endif %}
