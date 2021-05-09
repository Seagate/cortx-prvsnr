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

Install python packages:
  pkg.installed:
    - pkgs:
      - vim-enhanced
      - jq
      - python2-pip
      - python3
      - python3-pip
    - reload_modules: true

Install AWS CLI:
  pip.installed:
    - name: awscli
    - upgrade: True
    # Absolute path to a virtual environment directory or absolute path to a pip executable
    # We want to install python3 paramiko so we use pip3 here
    - bin_env: '/usr/bin/pip3'
    - require:
      - pkg: Install python packages

Install awscli-plugin-endpoint:
  pip.installed:
    - name: awscli-plugin-endpoint
    - upgrade: True
    # Absolute path to a virtual environment directory or absolute path to a pip executable
    # We want to install python3 paramiko so we use pip3 here
    - bin_env: '/usr/bin/pip3'
    - require:
      - pkg: Install python packages
