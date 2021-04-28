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

Install JDK:
  pkg.installed:
    - name: java-1.8.0-openjdk-headless

# Install elasticsearch:
#   pkg.installed:
#     - name: opendistroforelasticsearch
#     - version: {{ pillar['commons']['version']['opendistroforelasticsearch'] }}

Install elasticsearch:
  cmd.run:
    - name: yum install opendistroforelasticsearch-1.12.0 --nogpgcheck

{#% if (grains['os_family'] and ('7.3.2-1' in salt['pkg_resource.version']('elasticsearch'))) %#}
# Downgrade elasticsearch to 6.8.8:
#   cmd.run:
#     - name: yum downgrade -y elasticsearch
{#% endif %#}

Install rsyslog extras:
  pkg.installed:
    - pkgs:
      - rsyslog-elasticsearch: {{ pillar ['commons']['version']['rsyslog-elasticsearch'] }}
      - rsyslog-mmjsonparse: {{ pillar ['commons']['version']['rsyslog-mmjsonparse'] }}

# Install elasticsearch:
#   pkg.installed:
#     - sources:
#       - elasticsearch: https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.3.2-x86_64.rpm
