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

{% if ('data0' in grains['ip4_interfaces']) and (grains['ip4_interfaces']['data0'][0]) -%}
{% set s3client_ip = grains['ip4_interfaces']['data0'][0] %}
{% else -%}
{% set s3client_ip = grains['ip4_interfaces'][pillar['cluster'][grains['id']]['network']['data']['public_interfaces'][0]][0] %}
{% endif -%}
Append /etc/hosts:
  file.blockreplace:
    - name: /etc/hosts
    - backup: False
    - marker_start: "#---s3client_start---"
    - marker_end: "#---s3client_end---"
    - append_if_not_found: True
    - template: jinja
    - content: {{ s3client_ip }}  s3.seagate.com sts.seagate.com iam.seagate.com  sts.cloud.seagate.com

Copy client certs:
  file.managed:
    - name: /etc/ssl/stx-s3-clients/s3/ca.crt
    - source: salt://components/s3clients/files/ca.crt
    - makedirs: True
    - force: True
    - mode: 444
