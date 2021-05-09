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

{% if "physical" in grains['virtual'] %}

Get enclosure_id for {{ grains['id'] }}:
  module.run:
    - controller_cli.fetch_enclosure_serial: []

{% else %}

# VM
  {% if grains['machine_id'] %}
    {% set machine_id = grains['machine_id'] %}
Get enclosure_id for {{ grains['id'] }}:
  cmd.run:
    - name: echo "enc_{{ machine_id }}" > /etc/enclosure-id
  {% else %}
Get enclosure_id for {{ grains['id'] }}:
  test.show_notification:
    - text: "Can't not set the enclosure id on VM as there is not machine id set on {{ grains['id'] }}"
  {% endif %}
{% endif %}

Replace enclosure id in grains:
    cmd.run:
      - name: 'enclosure_id=`cat /etc/enclosure-id`; sed -ie "s/enclosure_id:*.*/enclosure_id: ${enclosure_id}/" /etc/salt/grains'
      - require:
        - Get enclosure_id for {{ grains['id'] }}

Sync grains data after refresh enclosure_id:
  module.run:
    - saltutil.refresh_grains: []
    - require:
      - Replace enclosure id in grains
    - watch_in:
      - Sync salt data
