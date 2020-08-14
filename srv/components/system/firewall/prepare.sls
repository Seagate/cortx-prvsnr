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

#To enable firewall IP table has to be disabled
Disable iptables:
  service.dead:
    - name: iptables
    - enable: False

Disable ip6tables:
  service.dead:
    - name: ip6tables
    - enable: False

Disable ebtables:
  service.dead:
    - name: ebtables
    - enable: False

# Mask the above to ensure they are never started
Mask iptables:
  service.masked:
    - name: iptables

Mask ip6tables:
  service.masked:
    - name: ip6tables

Mask ebtables:
  service.masked:
    - name: ebtables
