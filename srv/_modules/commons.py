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


def _update_dict(source_dict = {}, reference_dict = {}):
  """ Update config file dict based on pillar dict

  Args:
    source_dict: Dictionary built from component config file.
    reference_dict: Dictionary obtained from component pillar.
  """
  if not (isinstance(source_dict, dict)or isinstance(reference_dict, dict) ):
    raise Exception("[ERROR   ]: non dict args passed to _modules/commons.py::_config_update")
  
  for key in list(reference_dict.keys()):
    if( key in source_dict and isinstance(source_dict[key], dict) and
         isinstance(reference_dict[key], dict)):
        _update_dict(source_dict[key], reference_dict[key])
    else:
        source_dict[key] = reference_dict[key]
  