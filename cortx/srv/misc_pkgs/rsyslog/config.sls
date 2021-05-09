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

include:
  - misc_pkgs.rsyslog.install

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
