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

{% for id in salt['pillar.get']('updated_keys', []) %}
salt_minion_{{ id }}_key_deleted:
  cmd.run:
    - name: salt-key -d {{ id }} -y
{% endfor %}

salt_master_configured:
  file.managed:
    - name: /etc/salt/master
    - source: salt://components/provisioner/salt_master/files/master
    - keep_source: True
    - backup: minion

# test.true will fail if the config is malformed
salt_master_config_is_good:
  cmd.run:
    - name: 'salt-run salt.cmd test.true > /dev/null'
    - require:
      - salt_master_configured

salt_master_pki_set:
  file.recurse:
    - name: /etc/salt/pki/master/
    - source: salt://provisioner/files/master/pki
    - clean: False
    - keep_source: True
    - maxdepth: 1

salt_master_enabled:
  service.enabled:
    - name: salt-master.service
    - require:
      - salt_master_configured
      - salt_master_pki_set

# TODO DRY copied from srv/components/provisioner/salt_master/config.sls
salt_master_restarted:
  cmd.run:
    # --local is required if salt-master is actually not running,
    #    since state might be called by salt-run as well
    - name: 'salt-call --local service.restart salt-master > /dev/null '
    - bg: True
    - require:
      - salt_master_config_is_good
    - watch:
      - file: salt_master_configured
      - file: salt_master_pki_set
