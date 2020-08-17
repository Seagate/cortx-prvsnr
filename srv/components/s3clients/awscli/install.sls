#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
