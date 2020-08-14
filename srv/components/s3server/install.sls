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

Install common runtime libraries:
  pkg.installed:
    - pkgs:
      - java-1.8.0-openjdk-headless
      - libxml2
      - libyaml
      - yaml-cpp
      - gflags
      - glog

Install s3server package:
  pkg.installed:
    - name: cortx-s3server
    - version: {{ pillar['s3server']['version']['cortx-s3server'] }}
    - refresh: True

Install cortx-s3iamcli:
  pkg.installed:
    - pkgs:
      - cortx-s3iamcli: {{ pillar['s3server']['version']['cortx-s3iamcli'] }}
      # - s3iamcli-devel
      # - s3server-debuginfo
