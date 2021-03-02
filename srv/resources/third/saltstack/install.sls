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

# TODO IMPROVE EOS-8473 salt version from pillar

# TODO IMPROVE EOS-8473 is it needed ???
# Remove any older saltstack if any.
# systemctl stop salt-minion salt-master || true
# yum remove -y salt-minion salt-master


# TODO TEST EOS-8473
saltstack_installed:
  pkg.installed:
    - pkgs:
      - salt-master
      - salt-minion


# TODO consider to switch to python3-pygit2 as salt recommends
#      once it would be availble better for target platforms
gitfs_fileserver_deps_installed:
  pkg.installed:
    - name: GitPython   # FIXME JBOD
    - onlyif: yum info GitPython


{% if (
    (salt['grains.get']('virtual') == 'container') and
    salt['pillar.get']('factory_setup:ha') and
    not salt['pillar.get']('factory_setup:glusterfs_docker')
) -%}

# TODO IMPROVE WORKAROUND
#      lvm2 is required by glusterfs and it hangs
#      for about 8 minutes on starting lvm2-monitor.service
#      once saltstack is installed.
#      That workaround resolves the issue by some reason.

lvm2_installed:
  pkg.installed:
    - pkgs:
      - lvm2
    - require_in:
      - saltstack_installed

{% endif %}
