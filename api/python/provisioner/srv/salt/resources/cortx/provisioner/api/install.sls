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

{% set api_distr = salt['pillar.get']('inline:provisioner:api:distr') %}
{% set install_dir = salt['pillar.get']('provisioner:install_dir', '/opt/seagate/cortx/provisioner') %}


{% if api_distr == 'pip' %}

set_env_vars:
  environ.setenv:
    - name: LC_ALL
    - value: en_US.UTF-8
    - update_minion: True


epel_release_installed:
  pkg.installed:
    - pkgs:
      - epel-release
    - unless: yum info python36-m2crypto

# to workaround some issues related to
# m2crypto compilation at pip-based installation time
m2crypto_precompiled_installed:
  pkg.installed:
    - pkgs:
      - python36-m2crypto
    - require:
      - epel_release_installed

# TODO consider different sources incuding remote, see the not below
api_installed:
  pip.installed:
    - name: {{ install_dir }}/api/python
#   the following also works
#   - name: git+http://github.com/Seagate/cortx-prvsnr#subdirectory=api/python
    - bin_env: /usr/bin/pip3
    - upgrade: False  # to reuse already installed dependencies
                      # that may come from rpm repositories
    - require:
      - set_env_vars
      - m2crypto_precompiled_installed

{% else %}

api_installed:
  pkg.installed:
    - pkgs:
      - python36-cortx-prvsnr

{% endif %}

prvsnrusers:
  group.present

# TODO IMPROVE EOS-8473 consider states instead
api_post_setup_applied:
  cmd.script:
    - source: salt://{{ fileroot_prefix }}provisioner/api/files/post_setup.sh

# XXX ??? is it actually required here:
#     related module is part of provisioner core rpm
# salt_dynamic_modules_synced:
#  cmd.run:
    # TODO IMPROVE EOS-9581: cmd.run is a workaround since
    # as a module.run it doens't work as expected
    # https://docs.saltstack.com/en/latest/ref/modules/all/salt.modules.saltutil.html
#    - name: 'salt-call saltutil.sync_all'
#    - onchanges:
#      - api_installed
