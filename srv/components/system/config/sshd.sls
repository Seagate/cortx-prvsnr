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

Comment default wheel conf:
  file.comment:
    - name: /etc/sudoers
    - regex: ^\%wheel.*ALL=\(ALL\).*ALL$
    - char: '#'

Set NOPASSWD for wheel:
  file.append:
    - name: /etc/sudoers
    - text:
      - "\n## Allows people in group wheel to run all commands without a password"
      - "%wheel        ALL=(ALL)       NOPASSWD: ALL"
