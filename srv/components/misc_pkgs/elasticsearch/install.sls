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

Install JDK:
  pkg.installed:
    - name: java-1.8.0-openjdk-headless

Install elasticsearch:
  pkg.installed:
    - name: elasticsearch-oss
    - version: {{ pillar['commons']['version']['elasticsearch-oss'] }}

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
