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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

Sync data:
  module.run:
    - saltutil.clear_cache: []
    - saltutil.sync_all: []
    - saltutil.refresh_grains: []
    - saltutil.refresh_modules: []
    - saltutil.refresh_pillar: []

{% import_yaml 'components/defaults.yaml' as defaults %}

{% if (not "RedHat" in grains['os']) or (not salt['cmd.shell']('subscription-manager list | grep -m1 -A4 -Pe "Product Name:.*Red Hat Enterprise Linux Server"|grep -Pe "Status:.*Subscribed"')) %}

# Adding repos here are redundent thing.
# These repos get added in prereq-script, setup-provisioner
#TODO Remove redundency
 
Cleanup yum repos directory:
  cmd.run:
    - name: rm -rf /etc/yum.repos.d/CentOS-*.repo
    - if: test -f /etc/yum.repos.d/CentOS-Base.repo

{% for repo in defaults.base_repos.centos_repos %}
add_{{repo.id}}_repo:
  pkgrepo.managed:
    - name: {{ repo.id }}
    - humanname: {{ repo.id }}
    - baseurl: {{ repo.url }}
    - gpgcheck: 0
    - require:
      - Cleanup yum repos directory
{% endfor %}
{%- endif %}

Configure yum:
  file.managed:
    - name: /etc/yum.conf
    - source: salt://components/system/files/etc/yum.conf

Reset EPEL:
  cmd.run:
    - name: rm -rf /etc/yum.repos.d/epel.repo.*
    - if: test -f /etc/yum.repos.d/epel.repo.rpmsave

Add EPEL repo:
  pkgrepo.managed:
    - name: {{ defaults.base_repos.epel_repo.id }}
    - humanname: epel
    - baseurl: {{ defaults.base_repos.epel_repo.url }}
    - gpgcheck: 0
    - require:
      - Reset EPEL
      - Configure yum

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

Add commons yum repo:
  pkgrepo.managed:
    - name: {{ defaults.commons.repo.id }}
    - enabled: True
    - humanname: commons
    - baseurl: {{ defaults.commons.repo.url }}
    - gpgcheck: 0
    - require:
      - Add EPEL repo

Clean yum local:
  cmd.run:
    - name: yum clean all
    - require:
      - Configure yum
      - Add commons yum repo
      - Add EPEL repo

Clean yum cache:
  cmd.run:
    - name: rm -rf /var/cache/yum
    - requrie: Clean yum local
