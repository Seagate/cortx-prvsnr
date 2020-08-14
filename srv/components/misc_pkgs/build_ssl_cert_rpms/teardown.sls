#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
