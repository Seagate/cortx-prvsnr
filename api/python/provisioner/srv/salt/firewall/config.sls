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

#Enable firewall service before configuring ports
include:
  - .start

saltmaster:
  firewalld.service:
    - name: saltmaster
    - ports:
      - 4505/tcp
      - 4506/tcp
      - 8301/tcp

# glusterfs:
#   firewalld.service:
#     - name: gluster
#     - ports:
#       - 24007/tcp

ssh:
  firewalld.service:
    - name: ssh
    - ports:
      - 22/tcp

public:
  firewalld.present:
    - name: public
    - services:
      - glusterfs
      - saltmaster
      - ssh

Reload firewalld:
  service.running:
    - name: firewalld
    - reload: True
