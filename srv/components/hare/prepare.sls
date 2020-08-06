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

Add hare yum repo:
  pkgrepo.managed:
    - name: {{ defaults.hare.repo.id }}
    - enabled: True
    - humanname: hare
    - baseurl: {{ defaults.hare.repo.url }}
    - gpgcheck: 1
    - gpgkey: {{ defaults.hare.repo.gpgkey }}

{% if salt["pillar.get"]('cluster:{0}:is_primary'.format(grains['id']), false) %}
Prepare cluster yaml:
  file.managed:
    - name: /var/lib/hare/cluster.yaml
    - source: salt://components/hare/files/cluster.cdf.tmpl
    - template: jinja
    - mode: 444
    - makedirs: True
{% endif %}
