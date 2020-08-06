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

{% import_yaml 'components/defaults.yaml' as defaults %}

Add nfs_prereqs yum repo:
  pkgrepo.managed:
    - name: {{ defaults.nfs.uploads_repo.id }}
    - enabled: True
    - humanname: nfs_uploads
    - baseurl: {{ defaults.nfs.uploads_repo.url }}
    - gpgcheck: 0

Add nfs yum repo:
  pkgrepo.managed:
    - name: {{ defaults.nfs.repo.id }}
    - enabled: True
    - humanname: nfs
    - baseurl: {{ defaults.nfs.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.nfs.repo.gpgkey }}

Copy kvsns.ini file:
  file.managed:
    - name: /etc/kvsns.d/kvsns.ini
    - source: salt://components/nfs/files/etc/kvsns.d/kvsns.ini
    - makedirs: True

Copy ganesha.conf file:
  file.managed:
    - name: /etc/ganesha/ganesha.conf
    - source: salt://components/nfs/files/etc/ganesha/ganesha.conf
    - makedirs: True
