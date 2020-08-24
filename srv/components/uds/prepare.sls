#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

{% import_yaml 'components/defaults.yaml' as defaults %}

Add uds yum repo:
  pkgrepo.managed:
    - name: {{ defaults.uds.repo.id }}
    - enabled: True
    - humanname: uds
    - baseurl: {{ defaults.uds.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.uds.repo.gpgkey }}

Create /var/csm directory:
  file.directory:
    - name: /var/csm
    - makedirs: True
    - mode: 700
    - user: csm
    - group: csm

Create /var/csm/tls directory:
  file.directory:
    - name: /var/csm/tls
    - makedirs: True
    - mode: 700
    - user: csm
    - group: csm
