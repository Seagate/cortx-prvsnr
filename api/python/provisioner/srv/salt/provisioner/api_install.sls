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
# please email opensource@seagate.com or cortx-questions@seagate.com."
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
