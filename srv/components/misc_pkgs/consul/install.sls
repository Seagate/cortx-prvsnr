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

include:
  - components.misc_pkgs.consul.prepare

Consul installed:
  archive.extracted:
    - name: /opt/consul/bin
    - source: https://releases.hashicorp.com/consul/1.6.2/consul_1.6.2_linux_amd64.zip
    - source_hash: https://releases.hashicorp.com/consul/1.6.2/consul_1.6.2_SHA256SUMS
    - source_hash_name: consul_1.6.2_linux_amd64.zip
    - enforce_toplevel: False
    - keep_source: True
    - clean: False
    - trim_output: True
    - user: consul
    - group: consul
    - if_missing: /opt/consul/bin/consul
    - require:
      - user: Create Consul user

Update Consul executable with required permissions:
  file.managed:
    - name: /opt/consul/bin/consul
    - user: consul
    - group: consul
    - mode: 755
    - require:
      - user: Create Consul user
