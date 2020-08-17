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

include:
# Clients
  - components.s3clients.awscli.teardown
  - components.s3clients.s3cmd.teardown


Remove S3 client certs:
  pkg.removed:
    - name: stx-s3-client-certs

Remove client cert rpm:
  file.absent:
    - name: /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

Remove cortx-s3iamcli:
  pkg.removed:
    - pkgs:
      - cortx-s3iamcli
      # - cortx-s3iamcli-devel

Delete s3clients checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.s3clients
