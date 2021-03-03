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


{% set onchanges = salt['pillar.get']('inline:saltstack:salt_minion:onchanges') %}
{% from './salt_minion/macros.sls' import salt_minion_configured with context %}


{{ salt_minion_configured(onchanges) }}


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
    - source: salt://saltstack/salt_minion/files/minions/{{ grains.id }}/pki
    - clean: True
    - keep_source: True
    - maxdepth: 0
    - onchanges_in:
      - file: salt_minion_onchanges

salt_minion_master_pki_set:
  file.managed:
    - name: /etc/salt/pki/minion/minion_master.pub
    - source: salt://provisioner/files/master/pki/master.pub
    - keep_source: True
    - backup: minion
    - template: jinja
    - onchanges_in:
      - file: salt_minion_onchanges
