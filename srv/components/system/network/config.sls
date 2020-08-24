#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

{% if ((pillar['cluster']['search_domains']) and (pillar['cluster']['dns_servers'])) %}
Modify resolv.conf:
  file.managed:
    - name: /etc/resolv.conf
    - source: salt://components/system/network/files/resolv.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - replace: True
    - create: True
    - allow_empty: True
{% else %}
No nw config to apply:
  test.show_notification:
    - text: "dns_servers and search_domains are not specified in cluster.sls"
{% endif %}

# lo:
#   network.managed:
#     - name: lo
#     - enabled: True
#     - type: eth
#     - nm_controlled: no
#     - userctl: no
#     - ipv6_autoconf: no
#     - enable_ipv6: true
#     - ipaddr: 127.0.0.1
#     - netmask: 255.0.0.0
#     - network: 127.0.0.0
#     - broadcast: 127.255.255.255

{# {% if pillar['cluster'][grains['id']]['network']['mgmt_nw']['ipaddr'] %}#}
# # Donot execute this block for DHCP settings on management network
{# {% if 'mgmt0' in grains['ip4_interfaces'] %}#}
{#   {% set mgmt_nw = 'mgmt0' %}#}
{# {% else %}#}
{#   {% set mgmt_nw = pillar['cluster'][grains['id']]['network']['mgmt_nw']['iface'][0] %}#}
{# {% endif %}#}
{#{% if pillar['cluster'][grains['id']]['network']['mgmt_nw']['gateway'] %}#}
# Network setup:
#   network.system:
#     - enabled: True
#     - hostname: {#{{ grains['fqdn'] }}#}
#     - apply_hostname: True
#     - gateway: {#{{ salt['pillar.get']("cluster:{0}:network:mgmt_nw:gateway".format(grains['id']), grains['ip4_gw']) }}#}
#     - gatewaydev: {#{{ mgmt_nw }}#}
#     - require_reboot: True
{#{% else %}#}
# Network config failure:
#   test.fail_without_changes:
#     - name: Network configuration in absense of Gateway IP results in node inaccessibility.
{#{% endif %}#}
{# {% endif %}#}
