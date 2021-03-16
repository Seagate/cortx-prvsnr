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

Remove USL cert file:
  file.absent:
    - names:
      - /var/csm/tls

#Stop service uds:
#  service.dead:
#    - name: uds
#    - enable: False

Remove uds package:
  pkg.purged:
    - name: uds

Delete uds yum repo:
  pkgrepo.absent:
    - name: {{ defaults.uds.repo.id }}

Remove uds service file:
  file.absent:
    - name: /usr/lib/systemd/system/uds.service

Delete uds checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx_configs/provisioner_generated/{{ grains['id'] }}.uds
