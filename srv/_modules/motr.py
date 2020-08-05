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

import os.path
import re
import sys

from shutil import copyfile

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call motr.conf_update "/etc/sysconfig/motr" motr


# def _read_pillar(ref_component_pillar: str) -> dict:
def _read_pillar(ref_component_pillar):
  return __pillar__[ref_component_pillar]


# def update(name: str, ref_pillar: str, type: str=None, backup: bool=True) -> bool:
def conf_update(name='/etc/sysconfig/motr', ref_pillar='motr', type=None, backup=True):
  """Update component config file.

  Args :
    name: Destination path of component config file to be updated
    ref_pillar: Reference section from pillar data for a component to be updated
    type: Type of config file YAML/INI
    backup: Backup config file before modification as bool (Default: True)
  """

  name =  name if name else '/etc/sysconfig/motr'
  ref_pillar = ref_pillar if ref_pillar else 'motr'

  if not os.path.exists(name):
    print("ERROR: Motr config file {0} doesn't exist.".format(name))
    return False

  pillar_data = _read_pillar(ref_pillar)
  # print("Pillar data: {0}".format(pillar_data))

  if backup:
    copyfile(name, name + '.bak')

  file_contents = ''
  with open(name, 'r') as fd:
    file_contents = fd.read()
    for k, v in pillar_data.items():
      file_contents = re.sub(r'.?{0}=.+'.format(k), str(k) + '=' + str(v), file_contents)
      # for line in file_contents:
      #   if k in line:
      #     file_contents = re.sub(r'(?<=MERO_M0D_BELOG_SIZE=).+', v, file_contents)
  
  with open(name, 'w') as fd:
    fd.write(file_contents)

  return True
