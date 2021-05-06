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

Install_base_packages:
  pkg.installed:
    - pkgs:
      - sudo
      - ipmitool
      - bind-utils
      - python3
      - rsync
      - ftp
      - sshpass
      - jq
    - reload_modules: True

Install policy packages for SELinux:
  pkg.installed:
    - pkgs:
      - policycoreutils
      - policycoreutils-python

# Install python-pip packages (version 2 and 3)
python-pip:
  pkg.installed:
    - pkgs:
      - python3-pip
    - reload_modules: True
    - bin_env: /usr/bin/pip
    - upgrade: True

Install cortx python dependencies:
  pip.installed:
    - requirements: salt://components/system/files/cortx_py_utils_requirements.txt
    - bin_env: /usr/bin/pip3
