import errno
import os
import sys
import yaml

from shutil import copyfile

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call s3server.conf_update "/opt/seagate/s3/conf/s3config.yaml" s3server

# def _read_pillar(ref_component_pillar: str) -> dict:
def _read_pillar(ref_component_pillar):
  return __pillar__[ref_component_pillar]


# def update(config_file: str, ref_pillar: str, type: str=None, backup: bool=True) -> bool:
def conf_update(
    config_file="/opt/seagate/s3/conf/s3config.yaml",
    ref_pillar="s3server",
    type=None,
    backup=True
  ):
  """Update component config file.

  Args :
    config_file: Destination path of component config file to be updated
    ref_pillar: Reference section from pillar data for a component to be updated
    type: Type of config file YAML/INI
    backup: Backup config file before modification as bool (Default: True)
  """
  pillar_dict = _read_pillar(ref_pillar)
  
  if not os.path.exists(config_file):
    print("[ERROR   ] Possible error with s3server installation.")
    raise FileNotFoundError(
      errno.ENOENT,
      os.strerror(errno.ENOENT),
      config_file
    )

  config_dict = {}
  with open(config_file, "r") as fd:
    try:
      config_dict = yaml.safe_load(fd)
    except yaml.YAMLError as yerr:
      print("Error parsing yaml file {0}".format(yerr))
      return False
    finally:
      if not config_dict:
        return False

  if backup:
    copyfile(config_file, config_file + '.bak')

  config_dict = _update_dict(config_dict, pillar_dict)
  yaml.add_representer(_BlockSeqList, _blockseqlist_rep)

  with open(config_file, 'w') as fd:
    yaml.dump(config_dict, fd)

  return True


def _update_dict(config_dict, pillar_dict):
  for key in list(config_dict.keys()):
    if key in pillar_dict:
      if isinstance(config_dict[key], dict):
        _update_dict(config_dict[key], pillar_dict[key])
      elif pillar_dict[key].__class__.__name__ == "list":
        config_dict[key] = _BlockSeqList(pillar_dict[key])
      else:
        config_dict[key] = pillar_dict[key]
  
  return config_dict


class _BlockSeqList( list ): pass


def _blockseqlist_rep(dumper, data):
  return dumper.represent_sequence(u'tag:yaml.org,2002:seq', data, flow_style = True)
