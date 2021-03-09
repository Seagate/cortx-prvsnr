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

Remove 3rd party and cortx repos:
  file.absent:
    - names:
      - '/etc/yum.repos.d/3rd_party_epel.repo'
      - '/etc/yum.repos.d/3rd_party_glusterfs.repo'
      - '/etc/yum.repos.d/3rd_party_saltstack.repo'
      - '/etc/yum.repos.d/cortx_iso.repo'
      - '/etc/yum.repos.d/3rd_party.repo'
      - '/etc/yum.repos.d/RELEASE_FACTORY.INFO'

Remove pip config and cache:
  file.absent:
    - names :
      - '/etc/pip.conf'
      - '~/.cache/pip'

