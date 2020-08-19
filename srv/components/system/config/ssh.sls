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

/root/.ssh:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
    - makedirs: True
    - force: True
    - recurse:
      - user
      - group
      - mode

/root/.ssh/id_rsa:
  file.managed:
    - source: salt://components/system/files/.ssh/id_rsa_prvsnr
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 600
    - create: True

/root/.ssh/id_rsa.pub:
  file.managed:
    - source: salt://components/system/files/.ssh/id_rsa_prvsnr.pub
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True

/root/.ssh/authorized_keys:
  file.managed:
    - source: salt://components/system/files/.ssh/authorized_keys
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True

/root/.ssh/known_hosts:
  file.managed:
    - source: salt://components/system/files/.ssh/known_hosts
    - replace: True
    - keep_source: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 644
    - create: True
    - template: jinja
