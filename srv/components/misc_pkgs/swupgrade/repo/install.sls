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

{% macro repo_added(release, source, source_type, repo_name, repo_params={}) %}


sw_upgrade_repo_added_{{ repo_name }}_{{ release }}:
  pkgrepo.managed:
    - name: sw_upgrade_{{ repo_name }}_{{ release }}
    - humanname: Cortx Upgrade repo {{ repo_name }}-{{ release }}
    {% if source_type == 'url' %}
    - baseurl: {{ source }}/{{ repo_name }}
    {% else %}
    - baseurl: file://{{ source }}/{{ repo_name }}
    {% endif %}
    - enabled: {{ repo_params.get('enabled', True) }}
    - gpgcheck: 0
    {% if source_type == 'iso' %}
    - require:
      - sw_upgrade_repo_iso_mounted_{{ release }}
    {% endif %}


sw_upgrade_repo_metadata_cleaned_{{ repo_name }}_{{ release }}:
  cmd.run:
    - name: yum --disablerepo="*" --enablerepo="sw_upgrade_{{ repo_name }}_{{ release }}" clean metadata

{% endmacro %}
