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

{% macro repo_added(release, source, source_type, repo_params={}) %}

    {% from './iso/mount.sls' import repo_mounted with context %}

    {% if source_type == 'iso' %}

        {% set iso_path = source + '.iso' %}

copy_repo_iso_{{ release }}:
  file.managed:
    - name: {{ iso_path }}
    - source: salt://misc_pkgs/swupdate/repo/files/{{ release }}.iso
    - makedirs: True
    - require_in:
      - sw_update_repo_iso_mounted_{{ release }}
      - sw_update_repo_added_{{ release }}


{{ repo_mounted(release, iso_path, source) }}

    {% elif source_type == 'dir' %}


copy_repo_dir_{{ release }}:
  file.recurse:
    - name: {{ source }}
    - source: salt://misc_pkgs/swupdate/repo/files/{{ release }}
    - require_in:
      - sw_update_repo_added_{{ release }}


    {% endif %}


sw_update_repo_added_{{ release }}:
  pkgrepo.managed:
    - name: sw_update_{{ release }}
    - humanname: Cortx Update repo {{ release }}
    {% if source_type == 'url' %}
    - baseurl: {{ source }}
    {% else %}
    - baseurl: file://{{ source }}
    {% endif %}
    - enabled: {{ repo_params.get('enabled', True) }}
    - gpgcheck: 0
    {% if source_type == 'iso' %}
    - require:
      - sw_update_repo_iso_mounted_{{ release }}
    {% endif %}


sw_update_repo_metadata_cleaned_{{ release }}:
  cmd.run:
    - name: yum --disablerepo="*" --enablerepo="sw_update_{{ release }}" clean metadata
    - require:
      - sw_update_repo_added_{{ release }}

{% endmacro %}
