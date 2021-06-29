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

{%- if "physical" in grains['virtual'] %}
{% set current_enclosure = "enclosure-" + ((grains['id']).split('-'))[1] %}
{%- set ctrl_a_ip = pillar['storage'][current_enclosure]['controller']['primary']['ip'] %}
{%- set user = pillar['storage'][current_enclosure]['controller']['user'] %}
{%- set secret = pillar['storage'][current_enclosure]['controller']['secret'] %}
{%- set ntp_server = pillar['system']['ntp']['time_server'] %}
{%- set time_zone = pillar['system']['ntp']['time_zone'] %}

Set NTP on enclosure:
  cmd.run:
    - name: sh /opt/seagate/cortx/provisioner/srv/components/controller/files/scripts/controller-cli.sh host -h {{ ctrl_a_ip }} -u {{ user }} -p {{ secret }} -n {{ ntp_server }} {{ time_zone }}

{% else %}

No NTP on VM:
  test.show_notification:
    - text: "Skipping the NTP configuration on controller for VM"

{% endif %}