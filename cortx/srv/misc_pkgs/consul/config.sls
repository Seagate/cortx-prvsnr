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
  - misc_pkgs.consul.prepare
  - misc_pkgs.consul.install

# Set consul in bash_profile:
#   file.blockreplace:
#     - name: ~/.bashrc
#     - marker_start: '# DO NOT EDIT: Consul binaries'
#     - marker_end: '# DO NOT EDIT: End'
#     - content: 'export PATH=/opt/consul:$PATH'
#     - append_if_not_found: True
#     - append_newline: True
#     - backup: False
#     - require:
#       - Consul installed

# Source bash_profile for nodejs addition:
#   cmd.run:
#     - name: source ~/.bashrc
#     - require:
#       - Set consul in bash_profile

Reload service daemons for consul-agent.service:
  cmd.run:
    - name: systemctl daemon-reload
    - require:
      - file: Create Consul Agent Service
      - Consul installed
