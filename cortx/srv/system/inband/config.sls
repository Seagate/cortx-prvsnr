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

Copy the config file:
  file.managed:
    - name: /etc/scsi-network-relay.conf
    {% if grains['id'] == 'srvnode-1' %}
    - source: salt://components/system/inband/files/scsi-network-relay_srvnode-1.conf
    {% elif grains['id'] == 'srvnode-2' %}
    - source: salt://components/system/inband/files/scsi-network-relay_srvnode-2.conf
    {% endif %}
    - template: jinja
    - replace: True
    - keep_source: False
    - makedirs: True
    - create: True
