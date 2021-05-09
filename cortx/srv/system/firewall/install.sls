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

Install firewalld:
  pkg.installed:
    - pkgs:
       - firewalld: latest

# Enable Firewalld
Unmask Firewall service:
  service.unmasked:
    - name: firewalld
    - require:
      - Install firewalld

# Ensure ssh works when the firwall servcie starts for the next time
Open public zone:
  firewalld.present:
    - name: public
    - default: True
    - prune_ports: False
    - services:
      - ssh
    - prune_services: False
    - prune_interfaces: False
    - require:
      - Ensure service running

Ensure service running:
  service.running:
    - name: firewalld
