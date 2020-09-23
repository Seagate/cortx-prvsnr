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

{% set rpm_root_dir = defaults.tmp_dir + "/s3certs/rpmbuild" %}
{% set rpm_sources_dir = rpm_root_dir + "/SOURCES" %}
{% set s3_certs_src = "stx-s3-certs-" + defaults.s3server.config.S3_VERSION + '-' + defaults.s3server.config.DEPLOY_TAG %}

Generate s3 certs:
  cmd.run:
    - name: /opt/seagate/s3server/ssl/generate_certificate.sh -f domain_input.conf
    - cwd: {{ rpm_sources_dir }}/{{ s3_certs_src }}

Copy s3 certs:
  cmd.run:
    - name: cp -r s3_certs_sandbox/* .
    - cwd: {{ rpm_sources_dir }}/{{ s3_certs_src }}

Remove sandbox:
  file.absent:
    - name: {{rpm_sources_dir}}/{{ s3_certs_src }}/s3_certs_sandbox

Create archive:
  module.run:
    - archive.tar:
      - options: czf
      - tarfile: {{ s3_certs_src }}.tar.gz
      - sources: {{ s3_certs_src }}
      - cwd: {{ rpm_sources_dir }}

Build s3server certs rpm:
  cmd.run:
    - name: rpmbuild -ba --define="_s3_certs_version {{ defaults.s3server.config.S3_VERSION }}" --define="_s3_certs_src {{ s3_certs_src }}" --define="_s3_domain_tag {{ defaults.s3server.config.S3_DOMAIN }}" --define="_s3_deploy_tag {{ defaults.s3server.config.DEPLOY_TAG }}" --define="_topdir {{ rpm_root_dir }}" /opt/seagate/s3server/s3certs/s3certs.spec
    - cwd: {{ rpm_sources_dir }}

Build s3client certs rpm:
  cmd.run:
    - name: rpmbuild -ba --define="_s3_certs_version {{ defaults.s3server.config.S3_VERSION }}" --define="_s3_certs_src {{ s3_certs_src }}" --define="_s3_domain_tag {{ defaults.s3server.config.S3_DOMAIN }}" --define="_s3_deploy_tag {{ defaults.s3server.config.DEPLOY_TAG }}" --define="_topdir {{ rpm_root_dir }}" /opt/seagate/s3server/s3certs/s3clientcerts.spec
    - cwd: {{ rpm_sources_dir }}

Copy s3server certs rpm:
  cmd.run:
    - name: cp {{ rpm_root_dir }}/RPMS/x86_64/stx-s3-certs-* /opt/seagate
    - require:
      - Build s3server certs rpm

Copy s3server client client rpm:
  cmd.run:
    - name: cp {{ rpm_root_dir }}/RPMS/x86_64/stx-s3-client-certs-* /opt/seagate
    - require:
      - Build s3client certs rpm
