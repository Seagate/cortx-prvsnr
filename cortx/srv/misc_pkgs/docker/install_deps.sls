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

# TODO test glusterfs-docker

# required for docker-formula
yum_versionlock_installed:
  pkg.installed:
    - names:
      - yum-plugin-versionlock
      # salt warns about that package when docker is being installed,
      # it's required for some non trivial rpm versions comparison
      - rpmdevtools

# required for internal docker_* states
# TODO might be outdated in system repositories
#      but looks like Salt is ok with that
python_docker_installed:
  pkg.installed:
    - name: python36-docker
