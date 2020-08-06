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

{% set node_version = pillar['commons']['version']['nodejs'] %}
# Nodejs install
# Extract Node.js:
#   archive.extracted:
#     - name: /opt/nodejs
#     - source: http://nodejs.org/dist/{{ node_version }}/node-{{ node_version }}-linux-x64.tar.xz
#     - source_hash: http://nodejs.org/dist/{{ node_version }}/SHASUMS256.txt.asc
#     - source_hash_name: node-{{ node_version }}-linux-x64.tar.xz
#     - keep_source: True
#     - clean: True
#     - trim_output: True

Extract Node.js:
  archive.extracted:
    - name: /opt/nodejs
    - source: http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/commons/node/node-{{ node_version }}-linux-x64.tar.xz
    - source_hash: http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/commons/node/SHASUMS256.txt.asc
    - source_hash_name: node-{{ node_version }}-linux-x64.tar.xz
    - keep_source: True
    - clean: True
    - trim_output: True
