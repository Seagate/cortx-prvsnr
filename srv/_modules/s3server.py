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
  __pillar__ = getattr(sys.modules[__name__], '__pillar__')
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
