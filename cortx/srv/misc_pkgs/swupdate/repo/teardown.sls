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

{% macro repo_absent(release, repo_dir) %}

    {% from './iso/unmount.sls' import repo_unmounted with context %}

{{ repo_unmounted(release, repo_dir) }}

sw_update_repo_iso_absent_{{ release }}:
  file.absent:
    - name: {{ repo_dir }}.iso
    - require:
      - sw_update_repo_iso_unmounted_{{ release }}


sw_update_repo_dir_absent_{{ release }}:
  file.absent:
    - name: {{ repo_dir }}
    - require:
      - sw_update_repo_absent_{{ release }}
      - sw_update_repo_iso_unmounted_{{ release }}


sw_update_repo_absent_{{ release }}:
  pkgrepo.absent:
    - name: sw_update_{{ release }}

# TODO IMPROVE EOS-14348 remove from file root as well

{% endmacro %}
