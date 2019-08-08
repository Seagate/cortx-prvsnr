# This file is for reference only and should not be used.

import os
import sys
import yaml

from shutil import copyfile

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call eos.conf_update "/opt/seagate/s3/conf/s3config.yaml" s3_pillar_data

# def _read_pillar(ref_component_pillar: str) -> dict:
def _read_pillar(ref_component_pillar):
  return __pillar__[ref_component_pillar]


# def update(config_file: str, ref_pillar: str, type: str=None, backup: bool=True) -> bool:
def conf_update(config_file = "/opt/seagate/s3/conf/s3config.yaml", ref_pillar = "s3server" , type=None, backup=True):
  """Update component config file.

  Args :
    config_file: Destination path of component config file to be updated
    ref_pillar: Reference section from pillar data for a component to be updated
    type: Type of config file YAML/INI
    backup: Backup config file before modification as bool (Default: True)
  """
  # print("Name: {0}".format(config_file))
  # print("Pillar ref: {0}".format(ref_pillar))
  pillar_dict = _read_pillar(ref_pillar)
  #print("Pillar dict: {0}".format(pillar_dict))
  #print("Config file dict: {0}".format(config_dict))
  
  if not os.path.exists(config_file):
    print("ERROR: S3server config file {0} doesn't exist.".format(config_file))
    return False

  with open(config_file,"r") as f:
    config_dict = yaml.load(f)

  if backup:
    copyfile(config_file, config_file + '.bak')

  update_dict(config_dict, pillar_dict)
 
  with open(config_file, 'w') as fd:
    yaml.dump(config_dict, fd)

  return True if config_dict else False


def update_dict(config_dict, pillar_dict):
  for key in list(config_dict.keys()):
    print(key)
    if key in pillar_dict:
      if isinstance(config_dict[key], dict):
        update_dict(config_dict[key], pillar_dict[key])
      else:
        config_dict[key] = pillar_dict[key]


