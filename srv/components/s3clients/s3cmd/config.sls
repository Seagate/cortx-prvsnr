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

Configure s3cmd:
  file.managed:
    - name: ~/.s3cfg
    - source: salt://components/s3clients/s3cmd/files/.s3cfg
    - keep_source: False
    - template: jinja
    - makedirs: True
    - replace: False
    - create: True
    - user: {{ salt['grains.get']('username') }}
    - group: {{ salt['grains.get']('groupname') }}
    - mode: 644

Create directory for s3cmd ssl certs:
  file.directory:
    - name: ~/.s3cmd/ssl
    - makedirs: True
    - clean: True
    - force: True

Copy certs:
  file.copy:
    - name: ~/.s3cmd/ssl/ca.crt
    - source: /etc/ssl/stx-s3-clients/s3/ca.crt
    - makedirs: True
    - preserve: True
