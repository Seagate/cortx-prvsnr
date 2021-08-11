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

include:
  - components.misc_pkgs.consul.stop

# Remove Consul:
#   file.absent:
#     - name: /opt/consul

# Remove consul from bash_profile:
#   file.blockreplace:
#     - name: ~/.bashrc
#     - marker_start: '# DO NOT EDIT: Consul binaries'
#     - marker_end: '# DO NOT EDIT: End'
#     - content: ''

# Source bash_profile for consul cleanup:
#   cmd.run:
#     - name: source ~/.bashrc

# Remove Consul data directory:
#   file.absent:
#     - name: /opt/consul/data

# Remove Consul config directory:
#   file.absent:
#     - name: /etc/consul.d

# Remove Consul agent config file:
#   file.absent:
#     - name: /etc/consul.d/consul.json

# Remove Consul server config file:
#   file.absent:
#     - name: /etc/consul.d/consul_server.json
#     - source: salt://components/misc_pkgs/consul/files/consul_server.json
#     - mode: 640
#     - template: jinja

# Remove Consul Agent Service:
#   file.absent:
#     - name: /etc/systemd/system/consul.service
#     - source: salt://components/misc_pkgs/consul/files/consul.service
#     - makedirs: True
#     - mode: 644

# Reload service daemons post consul-agent.service removal:
#   cmd.run:
#     - name: systemctl daemon-reload

# Remove Consul user:
#   user.absent:
#     - name: consul

Remove consul package:
  cmd.run:
    - name: "rpm -e --nodeps consul"

Delete consul checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.consul
