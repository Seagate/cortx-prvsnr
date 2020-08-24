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

{% macro repo_absent(release, repo_dir) %}

    {% from './iso/unmount.sls' import repo_unmounted with context %}

{{ repo_unmounted(release, repo_dir) }}

cortx_base_repo_iso_absent_{{ release }}:
  file.absent:
    - name: {{ repo_dir }}.iso
    - require:
      - cortx_base_repo_iso_unmounted_{{ release }}


cortx_base_repo_dir_absent_{{ release }}:
  file.absent:
    - name: {{ repo_dir }}
    - require:
      - cortx_base_repo_absent_{{ release }}
      - cortx_base_repo_iso_unmounted_{{ release }}


cortx_base_repo_absent_{{ release }}:
  pkgrepo.absent:
    - name: cortx_base_{{ release }}

{% endmacro %}
