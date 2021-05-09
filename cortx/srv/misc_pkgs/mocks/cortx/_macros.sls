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

# TODO: use path from pillars or any other configuration
{% set salt_root = '/opt/seagate/cortx/provisioner/srv' %}

{% macro bundle_built(out_dir, out_type, version, gen_iso=False) %}

{{ out_dir }}:
  file.directory:
    - mode: 755
    - makedirs: True

build_mock_repo_{{ out_dir }}:
  cmd.run:
    - name: bash {{ salt_root }}/{{ tpldir }}/files/scripts/buildbundle.sh -v -o {{ out_dir }} -t {{ out_type }} -r {{ version }} {{ version }} {{ '--gen-iso' if gen_iso else ''}}
    - creates: {{ out_dir }}/RELEASE.INFO
    - require:
      - file: {{ out_dir }}

{% endmacro %}
