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

Sync data:
  module.run:
    - saltutil.clear_cache: []
    - saltutil.sync_all: []
    - saltutil.refresh_grains: []
    - saltutil.refresh_modules: []
    - saltutil.refresh_pillar: []

{% import_yaml 'components/defaults.yaml' as defaults %}

{% if pillar['release']['type'] != 'bundle' %}

{% if (not "RedHat" in grains['os']) or (not salt['cmd.shell']('subscription-manager list | grep -m1 -A4 -Pe "Product Name:.*Red Hat Enterprise Linux Server"|grep -Pe "Status:.*Subscribed"')) %}

# Adding repos here are redundent thing.
# These repos get added in prereq-script, setup-provisioner
#TODO Remove redundency
 
Cleanup yum repos directory:
  cmd.run:
    - name: rm -rf /etc/yum.repos.d/CentOS-*.repo
    - if: test -f /etc/yum.repos.d/CentOS-Base.repo

# {% for repo in defaults.base_repos.centos_repos %}
# add_{{repo.id}}_repo:
#   pkgrepo.managed:
#     - name: {{ repo.id }}
#     - humanname: {{ repo.id }}
#     - baseurl: {{ repo.url }}
#     - gpgcheck: 0
#     - require:
#       - Cleanup yum repos directory
#     - onlyif: test -z /etc/yum.repos.d/{{ repo.id }}.repo
# {% endfor %}
# {%- endif %}  # not (redhat && subscription)

Configure yum:
  file.managed:
    - name: /etc/yum.conf
    - source: salt://components/system/files/etc/yum.conf

# Reset EPEL:
#   cmd.run:
#     - name: rm -rf /etc/yum.repos.d/epel.repo.*
#     - if: test -f /etc/yum.repos.d/epel.repo.rpmsave

# Add EPEL repo:
#   pkgrepo.managed:
#     - name: {{ defaults.base_repos.epel_repo.id }}
#     - humanname: 3rd_party_epel
#     - baseurl: {{ defaults.base_repos.epel_repo.url }}
#     - gpgcheck: 0
# {% if pillar['release']['type'] != 'bundle' %}
#     - require:
#       - Reset EPEL
#       - Configure yum
# {% endif %}

# {% endif %}  # not a bundled release

# Add Saltsatck repo:
#   pkgrepo.managed:
#     - name: {{ defaults.base_repos.saltstack_repo.id }}
#     - humanname: saltstack
#     - baseurl: {{ defaults.base_repos.saltstack_repo.url }}
#     - gpgcheck: 1
#     - gpgkey: {{ defaults.base_repos.saltstack_repo.url }}/SALTSTACK-GPG-KEY.pub
#     - priority: 1
#     - require:
#       - Add EPEL repo

# Add commons yum repo:
#   pkgrepo.managed:
#     - name: {{ defaults.commons.repo.id }}
#     - enabled: True
#     - humanname: commons
#     - baseurl: {{ defaults.commons.repo.url }}
#     - gpgcheck: 0
#     - onlyif: test -z /etc/yum.repos.d/{{ defaults.commons.repo.id }}.repo
# {% if pillar['release']['type'] != 'bundle' %}
#     - require:
#       - Add EPEL repo
# {% endif %}

Clean yum local:
  cmd.run:
    - name: yum clean all
{% if pillar['release']['type'] != 'bundle' %}
    - require:
#      - Add commons yum repo
      - Configure yum
#      - Add EPEL repo
{% endif %}

Clean yum cache:
  cmd.run:
    - name: rm -rf /var/cache/yum
    - requrie: Clean yum local
