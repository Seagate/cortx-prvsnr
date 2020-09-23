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

{% import_yaml 'components/defaults.yaml' as defaults %}

{% set rpm_sources_dir = defaults.tmp_dir + "/s3certs/rpmbuild/SOURCES/" %}
{% set s3_certs_src = "stx-s3-certs-" + defaults.s3server.config.S3_VERSION + '-' + defaults.s3server.config.DEPLOY_TAG %}

Copy s3 utils:
  file.recurse:
    - name: /opt/seagate/s3server/
    - source: salt://components/misc_pkgs/build_ssl_cert_rpms/files/
    - user: root
    - group: root
    - file_mode: 750
    - dir_mode: 640
    - keep_source: False
    - clean: True
    - replace: True
    - template: jinja

Clean slate:
  file.absent:
    - name: {{ rpm_sources_dir }}

Create rpm sources dir:
  file.directory:
    - name: {{ rpm_sources_dir }}
    - user: root
    - group: root
    - dir_mode: 640
    - file_mode: 750
    - recurse:
      - user
      - group
      - mode
    - clean: True
    - makedirs: True

Ensure s3 certs dir:
  file.directory:
    - name: {{ rpm_sources_dir }}/{{ s3_certs_src }}
    - user: root
    - group: root
    - dir_mode: 640
    - file_mode: 750
    - recurse:
      - user
      - group
      - mode
