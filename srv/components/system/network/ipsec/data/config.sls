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

Data interface config for ifcfg-IPSec channel:
  file.managed:
    - name: /etc/sysconfig/network-scripts/ifcfg-ipsec-data0
    - source: salt://components/system/network/ipsec/data/files/ifcfg-ipsec-data0
    - user: root
    - group: root
    - mode: 644
    - template: jinja

Data interface config for keys-IPSec channel:
  file.managed:
    - name: /etc/sysconfig/network-scripts/keys-ipsec-data0
    - source: salt://components/system/network/ipsec/data/files/keys-ipsec-data0
    - user: root
    - group: root
    - mode: 600
