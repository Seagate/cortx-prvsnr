#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

{%- if (pillar['cluster'][node]['network']['mgmt_nw']['ipaddr']) and (not pillar['cluster'][grains['id']]['network']['mgmt_nw']['gateway']) %}
Management network config failure:
  test.fail_without_changes:
    - name: Static network configuration in absense of Gateway IP would result in node inaccessibility.
{% endif %}

{% set node = grains['id'] %}

Ensure bonding config for management bond:
  file.managed:
    - name: /etc/modprobe.d/bonding.conf
    - contents: options bonding max_bonds=0

# Setup network for management interfaces
{% for iface in pillar['cluster'][node]['network']['mgmt_nw']['iface'] %}
{{ iface }}:
  network.managed:
    - device: {{ iface }}
    - enabled: True
    - type: slave
    - master: mgmt0

Shutdown {{ iface }}:
  cmd.run:
    - name: ifdown {{ iface }}
    - onlyif: '[ "up" == "$(cat /sys/class/net/{{iface}}/operstate)" ]'
{% endfor %}

Setup mgmt0 bonding:
  network.managed:
    - name: mgmt0
    - type: bond
    - enabled: True
    - nm_controlled: no
    - userctl: no
    - defroute: yes
    # - slaves: em1 em2
    - mtu: 1500
    - mode: active-backup
    - miimon: 100
{% if pillar['cluster'][node]['network']['mgmt_nw']['ipaddr'] %}
    - proto: none
    - ipaddr: {{ pillar['cluster'][node]['network']['mgmt_nw']['ipaddr'] }}
{% if pillar['cluster'][node]['network']['data_nw']['netmask'] %}
    - netmask: {{ pillar['cluster'][node]['network']['data_nw']['netmask'] }}
{%- endif %}
{% if pillar['cluster'][node]['network']['data_nw']['gateway'] %}
    - gateway: {{ pillar['cluster'][grains['id']]['network']['mgmt_nw']['gateway'] }}
{% endif %}
{%- else %}
    - proto: dhcp
{%- endif %}

include:
  - components.system.network.config
