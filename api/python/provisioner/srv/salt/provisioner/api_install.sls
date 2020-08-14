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

m2crypto_precompiled_installed:
  pkg.installed:
    - pkgs:
      - python36-m2crypto

api_installed:
  pip.installed:
    - name: /opt/seagate/cortx/provisioner/api/python
    - bin_env: /usr/bin/pip3
    - upgrade: False  # to reuse already installed dependencies
                      # that may come from rpm repositories

prvsnrusers:
  group.present

# TODO IMPROVE EOS-8473 consider states instead
api_post_setup_applied:
  cmd.script:
    - source: salt://provisioner/files/post_setup.sh

salt_dynamic_modules_synced:
  cmd.run:
    # TODO IMPROVE EOS-9581: cmd.run is a workaround since
    # as a module.run it doens't work as expected
    # https://docs.saltstack.com/en/latest/ref/modules/all/salt.modules.saltutil.html
    - name: 'salt-call saltutil.sync_all'
    - onchanges:
      - api_installed
