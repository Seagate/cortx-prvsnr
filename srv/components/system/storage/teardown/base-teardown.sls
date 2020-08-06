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

# Setup SWAP and /var/mero
{% set node = grains['id'] %}

{% if "physical" in grains['virtual'] %}
# /boot/efi  (note: this is partition #1)
Remove EFI partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 1

# /boot  (note: this is partition #2)
Remove boot partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 2

# The rest of the OS partitions (except /var/crash) (note: this is partition #3)
Remove OS partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 3

# /var/crash (not under RAID or LVM control; size ~1TB; note: this is partition #4)
# Remove var_crash partition:
#   module.run:
#     - partition.rm:
#       - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
#       - minor: 4
# done with the OS partitions

Unmount SWAP:
  module.run:
    - mount.swapoff:
      - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}4

Remove swap from fstab:
  module.run:
    - mount.rm_fstab:
      - name: none
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}4

Remove swap partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 4

Unmount /var/mero partition:
  mount.unmounted:
    - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}5

Remove /var/mero partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 5
{% else %}
Unmount SWAP:
  module.run:
    - mount.swapoff:
      - name: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1

Remove swap from fstab:
  module.run:
    - mount.rm_fstab:
      - name: none
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1
    # - onlyif: grep {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}1 /etc/fstab

Remove swap partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 1

Unmount /var/mero partition:
  mount.unmounted:
    - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}2

Remove /var/mero partition:
  module.run:
    - partition.rm:
      - device: {{ pillar['cluster'][node]['storage']['metadata_device'][0] }}
      - minor: 2
{% endif %}

Refresh partition:
  module.run:
    - partition.probe: []
