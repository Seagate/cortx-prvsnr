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

import errno
import os
import sys
import yaml

from shutil import copyfile

import commons

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call s3server.conf_update "/opt/seagate/cortx/provisioner/srv/_modules/files/samples/s3config.yaml" s3server

# def _read_pillar(ref_component_pillar: str) -> dict:
def _read_pillar(ref_component_pillar):
  return __pillar__[ref_component_pillar]


# def update(name: str, ref_pillar: str, backup: bool=True) -> bool:
def conf_update(
    name="/opt/seagate/s3/conf/s3config.yaml",
    ref_pillar="s3server",
    backup=True
  ):
  """Update component config file.

  Args :
    name: Destination path of component config file to be updated
    ref_pillar: Reference section from pillar data for a component to be updated
    backup: Backup config file before modification as bool (Default: True)
  """
  pillar_dict = _read_pillar(ref_pillar)
  
  if not os.path.exists(name):
    print("[ERROR   ] Possible error with s3server installation.")
    raise FileNotFoundError(
      errno.ENOENT,
      os.strerror(errno.ENOENT),
      name
    )

  config_dict = {}
  with open(name, "r") as fd:
    try:
      config_dict = yaml.safe_load(fd)
    except yaml.YAMLError as yerr:
      print("Error parsing yaml file {0}".format(yerr))
      return False
    finally:
      if not config_dict:
        return False

  if backup:
    copyfile(name, name + '.bak')

  config_dict = commons._update_dict(config_dict, pillar_dict)
  yaml.add_representer(list, _blockseqlist_rep)
  yaml.add_representer(type(None), _represent_none)

  with open(name, 'w') as fd:
    yaml.dump(
        config_dict,
        stream=fd,
        default_flow_style = False,
        canonical=False,
        width=1,
        indent=4
    )

  return True


# def _update_dict(config_dict, pillar_dict):
#   for key in list(config_dict.keys()):
#     if key in pillar_dict:
#       if isinstance(config_dict[key], dict):
#         _update_dict(config_dict[key], pillar_dict[key])
#       else:
#         config_dict[key] = pillar_dict[key]
  
#   return config_dict


def _blockseqlist_rep(dumper, data):
  return dumper.represent_sequence(u'tag:yaml.org,2002:seq', data, flow_style = True)

def _represent_none(dumper, _):
  return dumper.represent_scalar('tag:yaml.org,2002:null', '~')
