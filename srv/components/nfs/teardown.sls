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
include:
  - components.nfs.stop

Remove NFS packages:
  pkg.removed:
    - pkgs:
      - cortx-dsal
      - cortx-dsal-devel
      - cortx-fs
      - cortx-fs-devel
      - cortx-fs-ganesha
      - cortx-fs-ganesha-test
      - cortx-nsal
      - cortx-nsal-devel
      - cortx-utils
      - cortx-utils-devel
    - disableexcludes: main

Remove NFS Ganesha:
  pkg.removed:
    - name: nfs-ganesha

Remove prereq packages for NFS:
  pkg.removed:
    - pkgs:
      - jemalloc
      - krb5-devel
      - libini_config-devel
      - krb5-server
      - nfs-utils
      - rpcbind
      - libevhtp
# Removing libblkid & krb5-libs removes systemd and
# other important system libraries, don't remove them.
      #- libblkid
      #- krb5-libs

# TODO Test
Delete kvsns.ini file:
  file.absent:
    - name: /etc/kvsns.d/kvsns.ini

Delete ganesha conf file:
  file.absent:
    - name: /etc/ganesha/ganesha.conf

Delete NFS yum repo:
  pkgrepo.absent:
    - name: {{ defaults.nfs.repo.id }}

Delete NFS uploads repo:
  pkgrepo.absent:
    - name: {{ defaults.nfs.uploads_repo.id }}

Delete nfs checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.nfs
