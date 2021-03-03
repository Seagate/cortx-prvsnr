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

{% macro salt_minion_configured(onchanges=None) %}

salt_minion_configured:
  file.managed:
    - name: /etc/salt/minion
    - source: salt://components/misc_pkgs/saltstack/salt_minion/files/minion
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
    - source: salt://components/misc_pkgs/saltstack/salt_minion/files/grains
    - keep_source: True
    - backup: minion
    - template: jinja

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
    - text: {{ f"on changes is { onchanges },  no action" }}

    {% endif %}

{% endmacro %}
