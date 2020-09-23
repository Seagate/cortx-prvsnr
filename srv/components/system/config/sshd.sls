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

Set ClientAliveInterval:
  file.replace:
    - name: /etc/ssh/sshd_config
    - pattern: ^ClientAliveInterval .*
    - repl: ClientAliveInterval 60
    - append_if_not_found: True

Set ClientAliveCountMax:
  file.replace:
    - name: /etc/ssh/sshd_config
    - pattern: ^ClientAliveCountMax .*
    - repl: ClientAliveCountMax 10000
    - append_if_not_found: True

Set SSH port:
  file.replace:
    - name: /etc/ssh/sshd_config
    - pattern: ^TCPKeepAlive .*
    - repl: TCPKeepAlive yes
    - append_if_not_found: True

Restart sshd service:
  service.running:
    - name: sshd
    - enable: True
    - reload: True
    - listen:
      - file: /etc/ssh/sshd_config

Configure wheel group access:
  file.managed:
    - name: /etc/sudoers.d/wheel_access
    - contents: |
        ## Allows people in group wheel to run all commands without a password
        %wheel        ALL=(ALL)       NOPASSWD: ALL
    - create: True
