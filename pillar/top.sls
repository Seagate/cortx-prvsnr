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

base:
  'G@roles:primary':
    - roles.primary
  '*':
    - ignore_missing: True
    - node_info.node_data
    - components.cluster                    # default all minions vars (here and below) TODO create task: move to groups.all.components...
    - components.commons
    - components.corosync-pacemaker
    - components.elasticsearch
    - components.motr
    - components.haproxy
    - components.openldap
    - components.release
    - components.s3clients
    - components.s3server
    - components.storage_enclosure
    - components.system
    - components.sspl
    - components.rabbitmq
    - components.rsyslog
    - components.uds
    - components.lustre
    - user.groups.all.*                     # user all minions vars (old style)
    - groups.all.*                     # all minions vars (new style)
  {{ grains.id }}:
    - ignore_missing: True
    - minions.{{ grains.id }}.*        # per-minion vars (new style)
    - user.minions.{{ grains.id }}.*   # user per-minion vars (old style)
