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

# Disable system swap
{% set swap_devices = salt['mount.swaps']().keys() %}
Deactivate and unmount system SWAP:
  module.run:
    # Deactivate SWAP
    {% for swap_device in swap_devices %}
    - mount.swapoff:
      - name: {{ swap_device }}
    {% endfor %}
    # Remove SWAP from /etc/fstab
    - mount.rm_fstab:
      - name: swap
      - device: /dev/mapper/vg_sysvol-lv_swap
