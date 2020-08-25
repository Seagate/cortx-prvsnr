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

{% macro repo_added(release, source, source_type, dest_repo_dir=None) %}

    {% from './iso/mount.sls' import repo_mounted with context %}

    {% if source_type == 'iso' %}

        {% set iso_path = dest_repo_dir + '.iso' %}

copy_repo_iso_{{ release }}:
  file.managed:
    - name: {{ iso_path }}
    - source: {{ source }}
    - makedirs: True
    - require_in:
      - repo_iso_mounted_{{ release }}
      - repo_added_{{ release }}

{{ repo_mounted(release, iso_path, dest_repo_dir) }}

    {% elif source_type == 'dir' %}


copy_repo_dir_{{ release }}:
  file.recurse:
    - name: {{ dest_repo_dir }}
    - source: {{ source }}
    - require_in:
      - repo_added_{{ release }}


    {% endif %}


repo_added_{{ release }}:
  pkgrepo.managed:
    - name: {{ release }}
    - humanname: Repository {{ release }}
    {% if source_type == 'url' %}
    - baseurl: {{ source }}
    {% else %}
    - baseurl: file://{{ dest_repo_dir }}
    {% endif %}
    - gpgcheck: 0
    {% if source_type == 'iso' %}
    - require:
      - repo_iso_mounted_{{ release }}
    {% endif %}


repo_metadata_cleaned_{{ release }}:
  cmd.run:
    - name: yum --disablerepo="*" --enablerepo="{{ release }}" clean metadata
    - require:
      - repo_added_{{ release }}

{% endmacro %}
