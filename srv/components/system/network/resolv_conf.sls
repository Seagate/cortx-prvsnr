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

# Configuration
{% if ((pillar['cluster']['search_domains']) and (pillar['cluster']['dns_servers'])) %}
Update resolv.conf:
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
No DNS config to apply:
  test.show_notification:
    - text: "dns_servers and search_domains are not specified in cluster.sls"
{% endif %}

