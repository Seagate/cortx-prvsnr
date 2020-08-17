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

salt_minion_configured:
  file.managed:
    - name: /etc/salt/minion
    - source: salt://provisioner/files/minions/all/minion
    - keep_source: True
    - backup: minion
    - template: jinja

# FIXME EOS-8473 prepend is not a clean solution
salt_minion_grains_configured:
  file.prepend:
    - name: /etc/salt/grains
    - sources:
      - salt://provisioner/files/minions/all/cluster_id
      - salt://provisioner/files/minions/{{ grains.id }}/grains
      - salt://provisioner/files/minions/{{ grains.id }}/node_id
      - salt://provisioner/files/minions/{{ grains.id }}/hostname_status

# TODO EOS-8473 better content management
salt_minion_id_set:
  file.prepend:
    - name: /etc/salt/minion_id
    - text: {{ grains.id }}

salt_minion_pki_set:
  file.recurse:
    - name: /etc/salt/pki/minion
    - source: salt://provisioner/files/minions/{{ grains.id }}/pki
    - clean: True
    - keep_source: True
    - maxdepth: 0

salt_minion_master_pki_set:
  file.managed:
    - name: /etc/salt/pki/minion/minion_master.pub
    - source: salt://provisioner/files/master/pki/master.pub
    - keep_source: True
    - backup: minion
    - template: jinja

salt_minion_enabled:
  service.enabled:
    - name: salt-minion.service
    - require:
      - salt_minion_configured
      - salt_minion_grains_configured
      - salt_minion_id_set
      - salt_minion_pki_set
      - salt_minion_master_pki_set

salt_minion_stopped:
  service.dead:
    - name: salt-minion.service
    - watch:
      - file: salt_minion_configured
      - file: salt_minion_grains_configured
      - file: salt_minion_id_set
      - file: salt_minion_pki_set
      - file: salt_minion_master_pki_set
