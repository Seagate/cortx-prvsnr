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

# TODO TEST OES-8473

{% set users = ['root'] %}
{% if pillar['node_specs'][grains['id']]['user'] != 'root' %}
  {% do users.append(pillar['node_specs'][grains['id']]['user']) %}
{% endif %}

{% for user in users %}

{% if user == 'root' %}
{%- set user_home = '/opt/test/root' -%}
{% else %}
{%- set user_home = '/opt/test/' + user -%}
{% endif %}

{{ user }}_ssh_dir_created:
  file.directory:
    - name: {{user_home}}/.ssh
    - mode: 700
    - user: {{ user }}
    - group: {{ user }}

{{ user }}_ssh_priv_key_deployed:
  file.managed:
    - show_changes: False
    - keep_source: True
    - mode: 600
    - names:
      - {{user_home}}/.ssh/id_rsa_prvsnr:
        - source: salt://provisioner/files/minions/all/id_rsa_prvsnr
      - {{user_home}}/.ssh/id_rsa:
        - source: salt://provisioner/files/minions/all/id_rsa_prvsnr
    - user: {{ user }}
    - group: {{ user }}
    - requires:
      - ssh_dir_created

{{ user }}_ssh_pub_key_deployed:
  file.managed:
    - keep_source: True
    - mode: 600
    - names:
      - {{user_home}}/.ssh/id_rsa_prvsnr.pub:
        - source: salt://provisioner/files/minions/all/id_rsa_prvsnr.pub
      - {{user_home}}/.ssh/id_rsa.pub:
        - source: salt://provisioner/files/minions/all/id_rsa_prvsnr.pub
    - user: {{ user }}
    - group: {{ user }}
    - requires:
      - ssh_dir_created

{{ user }}_ssh_key_authorized:
  ssh_auth.present:
    - source: {{user_home}}/.ssh/id_rsa_prvsnr.pub
    - user: {{ user }}
    - group: {{ user }}
    - requires:
      - ssh_pub_key_deployed

{{ user }}_ssh_config_updated:
  file.managed:
    - name: {{user_home}}/.ssh/config
    - contents: |
        {% for node_id, node in pillar['node_specs'].items() %}
        Host {{ node['host'] }}
            HostName {{ node['host'] }}
            Port {{ node['port'] }}
            User {{ node['user'] }}
            UserKnownHostsFile /dev/null
            StrictHostKeyChecking no
            IdentityFile {{user_home}}/.ssh/id_rsa_prvsnr
            IdentitiesOnly yes
            LogLevel ERROR
            BatchMode yes
        Host {{ node_id }} {{ node['host'] }}
            HostName {{ node['host'] }}
            Port {{ node['port'] }}
            User {{ node['user'] }}
            UserKnownHostsFile /dev/null
            StrictHostKeyChecking no
            IdentityFile {{user_home}}/.ssh/id_rsa_prvsnr
            IdentitiesOnly yes
            LogLevel ERROR
            BatchMode yes
        {% endfor %}
    - mode: 600
    - user: {{ user }}
    - group: {{ user }}

{% endfor %}
