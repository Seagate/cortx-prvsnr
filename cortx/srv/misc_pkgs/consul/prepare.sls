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

# Create Consul user:
#   user.present:
#     - name: consul
#     - home: /etc/consul.d
#     - system: True
#     - shell: /bin/false

# Create Consul bin directory:
#   file.directory:
#     - name: /opt/consul/bin
#     - makedirs: True
#     - dir_mode: 755
#     - file_mode: 644
#     - user: consul
#     - group: consul
#     - recurse:
#       - user
#       - group
#       - mode
#     - require:
#       - user: Create Consul user

# Create Consul data directory:
#   file.directory:
#     - name: /opt/consul/data
#     - makedirs: True
#     - dir_mode: 755
#     - file_mode: 644
#     - user: consul
#     - group: consul
#     - recurse:
#       - user
#       - group
#       - mode
#     - require:
#       - user: Create Consul user

# Create Consul config directory:
#   file.directory:
#     - name: /etc/consul.d
#     - makedirs: True
#     - dir_mode: 750
#     - file_mode: 640
#     - user: consul
#     - group: consul
#     - recurse:
#       - user
#       - group
#       - mode
#     - require:
#       - user: Create Consul user

# Create Consul server config file:
#   file.managed:
#     - name: /etc/consul.d/consul_server.json
#     - source: salt://components/misc_pkgs/consul/files/consul_server.json.j2
#     - mode: 640
#     - template: jinja
#     - user: consul
#     - group: consul
#     - require:
#       - user: Create Consul user

# Create Consul Agent Service:
#   file.managed:
#     - name: /etc/systemd/system/consul.service
#     - source: salt://components/misc_pkgs/consul/files/consul.service
#     - makedirs: True
#     - mode: 640
#     - template: jinja
