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

storage_mc:
  name: Gallium-NX3-m06   # equivalent to fqdn for server node
  #metadata_vols:

  virtual_volumes:
    poolA:
      type: virtual #virtual or lenear
      disks_range: 0.0-41
      nvols: 8
      size: 10TB
      mappings:
        map_vols: no  #yes/no
        host_initiator1:
          id: #0x21000024ff6c505d # initiator id
          access_mode: rw  #options: ro, rw, na
        host_initiator2:
          id: #0x21000024ff6c505d # initiator id
          access_mode: rw  #options: ro, rw, na
    poolB:
      type: virtual #virtual or lenear
      disks_range: 0.0-41
      nvols: 8
      size: 10TB
      mappings:
        map_vols: no
        host_initiator1:
          id: #0x21000024ff6c505d # initiator id
          access_mode: rw  #options: ro, rw, na
        host_initiator2:
          id: #0x21000024ff6c505d # initiator id
          access_mode: rw  #options: ro, rw, na
