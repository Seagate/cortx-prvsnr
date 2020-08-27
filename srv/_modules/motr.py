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
# please email opensource@seagate.com or cortx-questions@seagate.com."
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
