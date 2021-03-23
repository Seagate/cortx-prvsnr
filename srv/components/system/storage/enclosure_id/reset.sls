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

{% set enclosure = "enclosure-" + ((grains['id']).split('-'))[1] %}

Delete old enclosure_id:
  file.absent:
    - name: /etc/enclosure-id

Reset enclosure_id from grains on {{ grains['id'] }}:
  file.line:
    - name: /etc/salt/grains
    - mode: replace
    - match: 'enclosure_id:'
    - content: "enclosure_id:"

Sync grains data after refreshing the enclosure_id:
  module.run:
    - saltutil.refresh_grains: []
