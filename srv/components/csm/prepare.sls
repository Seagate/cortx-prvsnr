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

Add CSM uploads repo:
  pkgrepo.managed:
    - name: {{ defaults.csm.uploads_repo.id }}
    - enabled: True
    - humanname: csm_uploads
    - baseurl: {{ defaults.csm.uploads_repo.url }}
    - gpgcheck: 0

Add CSM repo:
  pkgrepo.managed:
    - name: {{ defaults.csm.repo.id }}
    - enabled: True
    - humanname: csm
    - baseurl: {{ defaults.csm.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.csm.repo.gpgkey }}

{% if 'single' not in pillar['cluster']['type'] %}
Render CSM ha input params template:
  file.managed:
    - name: /opt/seagate/cortx/ha/conf/build-ldr1-ha-csm-args.yaml
    - source: salt://components/csm/files/ha-params.tmpl
    - template: jinja
    - mode: 444
    - makedirs: True
{% endif %}
