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

{% if salt['pillar.get']('system:service-user:secret') %}

    {% set base_dir = '/opt/seagate/users' %}
    {% set user_data = salt['pillar.get']('system:service-user') %}

seagate_users_dir_created:
  file.directory:
    - name: {{ base_dir }}
    - user: root
    - group: root
    - mode: 755

service_user_configured:
  user.present:
    - name: {{ user_data['name'] }}
    - password: {{ salt['lyveutils.decrypt']('system', user_data['secret']) }}
    - hash_password: True
    - home: {{ base_dir }}/{{ user_data['name'] }}
    - shell: {{ user_data['shell'] }}
    - groups: {{ user_data['groups'] }}
    # would be activated at unboxing time
    {% if not "primary" in pillar["cluster"][grains["id"]]["roles"] -%}
    - expire: 1
    {% endif %}

{% else %}

no_password:
  test.nop: []

{% endif %}
