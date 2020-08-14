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

# TODO TEST OES-8473

ssh_dir_created:
  file.directory:
    - name: /root/.ssh
    - mode: 700

ssh_priv_key_deployed:
  file.managed:
    - name: /root/.ssh/id_rsa_prvsnr
    - source: salt://provisioner/files/minions/all/id_rsa_prvsnr
    - show_changes: False
    - keep_source: True
    - mode: 600
    - requires:
      - ssh_dir_created

ssh_pub_key_deployed:
  file.managed:
    - name: /root/.ssh/id_rsa_prvsnr.pub
    - source: salt://provisioner/files/minions/all/id_rsa_prvsnr.pub
    - keep_source: True
    - mode: 600
    - requires:
      - ssh_dir_created

ssh_key_authorized:
  ssh_auth.present:
    - source: /root/.ssh/id_rsa_prvsnr.pub
    - user: root
    - requires:
      - ssh_pub_key_deployed

ssh_config_updated:
  file.managed:
    - name: /root/.ssh/config
    - source: salt://ssh/files/config
    - keep_source: True
    - mode: 600
    - template: jinja
