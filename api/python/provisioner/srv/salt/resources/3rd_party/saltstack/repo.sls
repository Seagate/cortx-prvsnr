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

{% set fileroot_prefix = salt['pillar.get']('inline:fileroot_prefix', '') %}

setup_yum_salt_repo:
  file.managed:
    - name: /etc/yum.repos.d/saltstack.repo
    - source: salt://{{ fileroot_prefix }}/saltstack/files/saltstack.repo
    - keep_source: True
    - backup: minion
    - onchanges_in:
      - clean_yum_salt_repo_metadata
      - import_yum_salt_repo_key

# TODO IMPROVE look for specific salt module instead of cmd.run
clean_yum_salt_repo_metadata:
  cmd.run:
    - name: yum --disablerepo="*" --enablerepo="saltstack" clean metadata

epel_release_installed:
  pkg.installed:
    - name: epel-release

# TODO IMPROVE look for specific salt module instead of cmd.run
# (https://repo.saltstack.com/#rhel, instructions for minor releases centos7 py3)
import_yum_salt_repo_key:
  cmd.run:
    - name: rpm --import https://repo.saltproject.io/py3/redhat/7/x86_64/archive/3002.2/SALTSTACK-GPG-KEY.pub
