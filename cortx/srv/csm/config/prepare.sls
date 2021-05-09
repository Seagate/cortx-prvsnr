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

Stage - Prepare CSM:
  cmd.run:
    - name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/cortx/csm/conf/setup.yaml', 'csm:prepare')
    - failhard: True

# {% import_yaml 'components/defaults.yaml' as defaults %}

# {% if pillar['release']['target_build'] %}
# Add CSM uploads repo:
#   pkgrepo.managed:
#     - name: {{ defaults.csm.uploads_repo.id }}
#     - enabled: True
#     - humanname: csm_uploads
#     - baseurl: {{ defaults.csm.uploads_repo.url }}
#     - gpgcheck: 0

# Add CSM repo:
#   pkgrepo.managed:
#     - name: {{ defaults.csm.repo.id }}
#     - enabled: True
#     - humanname: csm
#     - baseurl: {{ defaults.csm.repo.url }}
#     - gpgcheck: 1
#     - gpgkey: {{ defaults.csm.repo.gpgkey }}
# {% endif %}

{#% set server_nodes = [ ] -%#}
{#% for node in pillar['cluster'].keys() -%#}
{#% if "srvnode-" in node -%#}
{#% do server_nodes.append(node)-%#}
{#% endif -%#}
{#% endfor -%#}
{#% if 1 < (server_nodes|length) %#}
# Render CSM ha input params template:
#   file.managed:
#     - name: /opt/seagate/cortx/ha/conf/build-ha-csm-args.yaml
#     - source: salt://components/csm/files/ha-params.tmpl
#     - template: jinja
#     - mode: 444
#     - makedirs: True
{#% endif %#}

