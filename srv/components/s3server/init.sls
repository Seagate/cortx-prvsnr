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

{% if not salt['file.file_exists']('/opt/seagate/cortx_configs/provisioner_generated/{0}.s3server'.format(grains['id'])) %}
include:
  - components.s3server.install
  - components.s3server.config
  - components.s3server.start
#  - components.s3server.sanity_check

Generate s3server checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.s3server
    - makedirs: True
    - create: True

{%- else -%}

S3Server already applied:
  test.show_notification:
    - text: "Storage states already run on node: {{ grains['id'] }}. Run 'salt '*' state.apply components.s3server.teardown' to reprovision these states."

{%- endif -%}
