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

{% macro salt_master_configured(updated_keys=None, onchanges=None) %}

{% set fileroot_prefix = salt['pillar.get']('inline:fileroot_prefix', '') %}

{% for id in (updated_keys or []) %}
salt_minion_{{ id }}_key_deleted:
  cmd.run:
    - name: salt-key -d {{ id }} -y
{% endfor %}

salt_master_pki_set:
  file.recurse:
    - name: /etc/salt/pki/master/
    - source: salt://{{ fileroot_prefix }}saltstack/salt-cluster/files/pki/master
    - clean: False
    - keep_source: True
    - maxdepth: 1
    - onchanges_in:
      - file: salt_master_onchanges

salt_master_configured:
  file.managed:
    - name: /etc/salt/master
    - source: salt://{{ fileroot_prefix }}saltstack/salt-master/files/config/master
    - keep_source: True
    - backup: minion

salt_master_config_is_good:
  cmd.run:
    - name: 'salt-run salt.cmd test.true > /dev/null'
    - onchanges:
      - file: salt_master_configured

salt_master_enabled:
  service.enabled:
    - name: salt-master.service
    - require:
      - salt_master_configured

{% if onchanges == 'restart' %}

salt_master_onchanges:
  cmd.run:
    # 1. test.true will prevent restart of salt-master if the config is malformed
    # 2. --local is required if salt-master is actually not running,
    #    since state might be called by salt-run as well
    - name: 'salt-run salt.cmd test.true > /dev/null && salt-call --local service.restart salt-master > /dev/null '
    - bg: True
    - require:
      - salt_master_config_is_good
    - onchanges:
      - file: salt_master_configured

{% endif %}

{% endmacro %}
