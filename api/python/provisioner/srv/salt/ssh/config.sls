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

ssh_dir_created:
  file.directory:
    - name: /root/.ssh
    - mode: 700

ssh_priv_key_deployed:
  file.managed:
    - show_changes: False
    - keep_source: True
    - mode: 600
    - names:
      - /root/.ssh/id_rsa_prvsnr:
        - source: salt://provisioner/files/minions/all/id_rsa_prvsnr
      - /root/.ssh/id_rsa:
        - source: salt://provisioner/files/minions/all/id_rsa_prvsnr
    - requires:
      - ssh_dir_created

ssh_pub_key_deployed:
  file.managed:
    - keep_source: True
    - mode: 600
    - names:
      - /root/.ssh/id_rsa_prvsnr.pub:
        - source: salt://provisioner/files/minions/all/id_rsa_prvsnr.pub
      - /root/.ssh/id_rsa.pub:
        - source: salt://provisioner/files/minions/all/id_rsa_prvsnr.pub
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
