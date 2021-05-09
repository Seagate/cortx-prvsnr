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

# include:
#   - misc_pkgs.consul.prepare

# Consul installed:
#   archive.extracted:
#     - name: /usr/bin
#     - source: https://releases.hashicorp.com/consul/1.6.2/consul_1.6.2_linux_amd64.zip
#     - source_hash: https://releases.hashicorp.com/consul/1.6.2/consul_1.6.2_SHA256SUMS
#     - source_hash_name: consul_1.6.2_linux_amd64.zip
#     - enforce_toplevel: False
#     - keep_source: True
#     - clean: False
#     - trim_output: True
#     - user: consul
#     - group: consul
#     - if_missing: /usr/bin/consul
#     - require:
#       - user: Create Consul user

# Update Consul executable with required permissions:
#   file.managed:
#     - name: /usr/bin/consul
#     - user: consul
#     - group: consul
#     - mode: 755
#     - require:
#       - user: Create Consul user

Consul installed:
  pkg.installed:
    - name: consul
    - version: {{ pillar['commons']['version']['consul'] }}
