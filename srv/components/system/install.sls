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

Install_base_packages:
  pkg.installed:
    - pkgs:
      - sudo
      - ipmitool
      - bind-utils
      - python3
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

Ensure cryptography python package absent:
  pip.removed:
    - name: cryptography
    - bin_env: /usr/bin/pip3

Install cryptography python package:
  pip.installed:
    - name: cryptography
    - bin_env: /usr/bin/pip3
    - target: /usr/lib64/python3.6/site-packages/
    - require:
      - Ensure cryptography python package absent

Install eos-py-utils:           # Package for cryptography
  pkg.installed:
    - name: eos-py-utils
    - requrie:
      - Install cryptography python package
