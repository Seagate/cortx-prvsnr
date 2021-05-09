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

Remove Packages:
  pkg.purged:
    - pkgs:
#      - openssl-libs       # Removing this breaks yum, ssh. Hence don't uncomment.
#      - openssl            # Removing this breaks yum, ssh. Hence don't uncomment.
      - rpm-build
      - java-1.8.0-openjdk-headless.x86_64

Remove certs:
  file.absent:
    - names:
      - {{ rpm_sources_dir }}
      - /opt/seagate/stx-s3-certs-1.0-1_s3dev.x86_64.rpm
      - /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm
