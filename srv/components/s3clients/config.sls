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


Append /etc/hosts:
  file.line:
    - name: /etc/hosts
    - mode: ensure
{% if 'data0' in grains['ip4_interfaces'] and grains['ip4_interfaces']['data0'] -%}
    - content: {{ grains['ip4_interfaces']['data0'] }}  s3.seagate.com sts.seagate.com iam.seagate.com   sts.cloud.seagate.com
{% else -%}
    - content: {{ grains['ip4_interfaces'][pillar['cluster'][grains['id']]['network']['data']['public_interfaces'][0]][0] }}  s3.seagate.com sts.seagate.com iam.seagate.com   sts.cloud.seagate.com
{% endif -%}%}
    - after: "::1.+localhost.+"
