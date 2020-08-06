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
  - components.misc_pkgs.rsyslog.install

Load UDP mod:
  file.line:
    - name: /etc/rsyslog.conf
    - content: "$ModLoad imudp"
    - match: "#$ModLoad imudp"
    - mode: replace
    - backup: True
    - require:
      - Install rsyslog service


Set UPD port:
  file.line:
    - name: /etc/rsyslog.conf
    - content: "$UDPServerRun 514"
    - match: "#$UDPServerRun 514"
    - mode: replace
    - require:
      - Install rsyslog service

Load TCP mod:
  file.line:
    - name: /etc/rsyslog.conf
    - content: "$ModLoad imtcp"
    - match: "#$ModLoad imtcp"
    - mode: replace
    - require:
      - Install rsyslog service

Set TCP port:
  file.line:
    - name: /etc/rsyslog.conf
    - content: "$InputTCPServerRun 514"
    - match: "#$InputTCPServerRun 514"
    - mode: replace
    - require:
      - Install rsyslog service
