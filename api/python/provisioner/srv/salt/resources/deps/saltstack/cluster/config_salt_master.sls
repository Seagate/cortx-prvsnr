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

{% set onchanges = salt['pillar.get']('inline:saltstack:salt_master:onchanges') %}
{% from '../salt_master/macros.sls' import salt_master_configured with context %}

{% for id in salt['pillar.get']('inline:saltstack:salt_master:updated_keys', []) %}
salt_minion_{{ id }}_key_deleted:
  cmd.run:
    - name: salt-key -d {{ id }} -y
{% endfor %}

salt_master_pki_set:
  file.recurse:
    - name: /etc/salt/pki/master/
    - source: salt://provisioner/files/master/pki
    - clean: False
    - keep_source: True
    - maxdepth: 1
    - onchanges_in:
      - file: salt_master_onchanges

{{ salt_master_configured(onchanges) }}
