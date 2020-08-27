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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

{% if not salt['file.file_exists']('/opt/seagate/cortx/provisioner/generated_configs/{0}.nfs'.format(grains['id'])) %}
include:
  - components.nfs.prepare
  - components.nfs.install
  #- components.nfs.config
  #- components.nfs.sanity_check

Generate nfs checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.nfs
    - makedirs: True
    - create: True
{%- else -%}
nfs already installed:
  test.show_notification:
    - text: "The nfs states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.nfs.teardown' to reprovision these states."
{% endif %}
