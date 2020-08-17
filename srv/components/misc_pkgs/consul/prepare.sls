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

Create Consul user:
  user.present:
    - name: consul
    - home: /etc/consul.d
    - system: True
    - shell: /bin/false

Create Consul bin directory:
  file.directory:
    - name: /opt/consul/bin
    - makedirs: True
    - dir_mode: 755
    - file_mode: 644
    - user: consul
    - group: consul
    - recurse:
      - user
      - group
      - mode
    - require:
      - user: Create Consul user

Create Consul data directory:
  file.directory:
    - name: /opt/consul/data
    - makedirs: True
    - dir_mode: 755
    - file_mode: 644
    - user: consul
    - group: consul
    - recurse:
      - user
      - group
      - mode
    - require:
      - user: Create Consul user

Create Consul config directory:
  file.directory:
    - name: /etc/consul.d
    - makedirs: True
    - dir_mode: 750
    - file_mode: 640
    - user: consul
    - group: consul
    - recurse:
      - user
      - group
      - mode
    - require:
      - user: Create Consul user

Create Consul agent config file:
  file.managed:
    - name: /etc/consul.d/consul.json
    - source: salt://components/misc_pkgs/consul/files/consul.json.j2
    - mode: 640
    - template: jinja
    - user: consul
    - group: consul
    - require:
      - user: Create Consul user

#Create Consul server config file:
#  file.managed:
#    - name: /etc/consul.d/consul_server.json
#    - source: salt://components/misc_pkgs/consul/files/consul_server.json.j2
#    - mode: 640
#    - template: jinja
#    - user: consul
#    - group: consul
#    - require:
#      - user: Create Consul user

Create Consul Agent Service:
  file.managed:
    - name: /etc/systemd/system/consul.service
    - source: salt://components/misc_pkgs/consul/files/consul.service
    - makedirs: True
    - mode: 640
    - template: jinja
