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

{% macro repo_added(release, source, source_type, dest_repo_dir=None, is_repo=True, enabled=True) %}

    {% from './iso/mount.sls' import repo_mounted with context %}

    {% if source_type == 'iso' %}

        {% set iso_path = dest_repo_dir + '.iso' %}

        {% if not salt['pillar.get']('skip_iso_copy', False) %}

copy_repo_iso_{{ release }}:
  file.managed:
    - name: {{ iso_path }}
    - source: {{ source }}
    - makedirs: True
    - require_in:
      - repo_iso_mounted_{{ release }}
      - repo_added_{{ release }}

        {% endif %}

{{ repo_mounted(release, iso_path, dest_repo_dir) }}

    {% elif source_type == 'dir' %}


copy_repo_dir_{{ release }}:
  file.recurse:
    - name: {{ dest_repo_dir }}
    - source: {{ source }}
    - require_in:
      - repo_added_{{ release }}


    {% endif %}


    {% if is_repo %}

repo_added_{{ release }}:
  pkgrepo.managed:
    - name: {{ release }}
    - humanname: Repository {{ release }}
    {% if source_type == 'url' %}
    - baseurl: {{ source }}
    {% else %}
    - baseurl: file://{{ dest_repo_dir }}
    {% endif %}
    - enabled: {{ enabled }}
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

    {% endif %}

{% endmacro %}
