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

{% if salt['pillar.get']('glusterfs:add_repo', False) %}

# TODO detect centos instead
    {% if "RedHat" not in grains['os'] %}

glusterfs_repo_is_installed:
  pkg.installed:
    - pkgs:
      - centos-release-gluster7

    {% else  %}

# FIXME need to use gluster from official  RedHat repos
# centos-release-gluster7 not available for redhat hence adding repo manually
glusterfs_repo_is_installed:
  pkgrepo.managed:
    - name: glusterfs
    - humanname: glusterfs-7
    - baseurl: http://mirror.centos.org/centos/7/storage/x86_64/gluster-7/
    - gpgcheck: 0
    - enabled: 1

    {% endif %}

{% endif %}
