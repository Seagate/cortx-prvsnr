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

{% import_yaml 'components/defaults.yaml' as defaults %}

Add nfs_prereqs yum repo:
  pkgrepo.managed:
    - name: {{ defaults.nfs.uploads_repo.id }}
    - enabled: True
    - humanname: nfs_uploads
    - baseurl: {{ defaults.nfs.uploads_repo.url }}
    - gpgcheck: 0

Add nfs yum repo:
  pkgrepo.managed:
    - name: {{ defaults.nfs.repo.id }}
    - enabled: True
    - humanname: nfs
    - baseurl: {{ defaults.nfs.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.nfs.repo.gpgkey }}

Copy kvsns.ini file:
  file.managed:
    - name: /etc/kvsns.d/kvsns.ini
    - source: salt://components/nfs/files/etc/kvsns.d/kvsns.ini
    - makedirs: True

Copy ganesha.conf file:
  file.managed:
    - name: /etc/ganesha/ganesha.conf
    - source: salt://components/nfs/files/etc/ganesha/ganesha.conf
    - makedirs: True
