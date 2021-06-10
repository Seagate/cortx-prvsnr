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

{% set onchanges = salt['pillar.get']('inline:salt-minion:onchanges') %}

# FIXME that fails intermittently with
#       Relative path "./macros.sls" cannot be resolved without an environment
#{ % from './macros.sls' import salt_minion_configured with context % }

#{ { salt_minion_configured(onchanges) } }

{% set fileroot_prefix = salt['pillar.get']('inline:fileroot_prefix', '') %}

salt_minion_configured:
  file.managed:
    - name: /etc/salt/minion
    - source: salt://{{ fileroot_prefix }}saltstack/salt-minion/files/config/minion
    - keep_source: True
    - backup: minion
    - template: jinja

salt_minion_config_is_good:
  cmd.run:
    - name: 'salt-call --local test.ping'
    - onchanges:
      - file: salt_minion_configured

# FIXME EOS-8473 prepend is not a clean solution
salt_minion_grains_configured:
  file.managed:
    - name: /etc/salt/grains
    - source: salt://{{ fileroot_prefix }}saltstack/salt-minion/files/config/grains
    - keep_source: True
    - backup: minion
    - template: jinja

# TODO EOS-8473 better content management
salt_minion_id_set:
  file.prepend:
    - name: /etc/salt/minion_id
    - text: {{ grains.id }}
    - onchanges_in:
      - file: salt_minion_onchanges

salt_minion_pki_set:
  file.recurse:
    - name: /etc/salt/pki/minion
    - source: salt://{{ fileroot_prefix }}saltstack/salt-cluster/files/pki/minions/{{ grains.id }}
    - clean: False
    - keep_source: True
    - maxdepth: 0
    - onchanges_in:
      - file: salt_minion_onchanges

salt_minion_master_pki_set:
  file.managed:
    - name: /etc/salt/pki/minion/minion_master.pub
    - source: salt://{{ fileroot_prefix }}saltstack/salt-cluster/files/pki/master/master.pub
    - keep_source: True
    - backup: minion
    - template: jinja
    - onchanges_in:
      - file: salt_minion_onchanges

salt_minion_enabled:
  service.enabled:
    - name: salt-minion.service
    - require:
      - salt_minion_configured
      - salt_minion_grains_configured


    {% if onchanges == 'stop' %}

salt_minion_onchanges:
  service.dead:
    - name: salt-minion.service
    - require:
      - salt_minion_config_is_good
    - onchanges:
      - file: salt_minion_configured
      - file: salt_minion_grains_configured

    {% elif onchanges == 'restart' %}

salt_minion_onchanges:
  cmd.run:
    - name: 'salt-call service.restart salt-minion'
    - bg: True
    - require:
      - salt_minion_config_is_good
    - onchanges:
      - file: salt_minion_configured
      - file: salt_minion_grains_configured

    {% else %}

salt_minion_onchanges:
  test.show_notification:
    - text: {{ "onchanges is " + onchanges + ", no action" }}

    {% endif %}
