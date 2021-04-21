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

# This file is for reference only and should not be used.

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call cortx.conf_update "/opt/seagate/s3/conf/s3config.yaml" s3server


import sys
import yaml


# def update(name: str, ref_pillar: str, type: str=None, backup: bool=True) -> bool:
def conf_update(name, ref_pillar, type=None, backup=True):
  """Update component config file.

  Args :
    name: Destination path of component config file to be updated
    ref_pillar: Reference section from pillar data for a component to be updated
    type: Type of config file YAML/INI
    backup: Backup config file before modification as bool (Default: True)
  """

  pillar_dict = _read_pillar(ref_pillar)
  config_dict = None
  if type and 'YAML' in type.upper():
    config_dict = _read_yaml(name)
  elif type and 'INI' in type.upper():
    config_dict = _read_ini(name)
  else:
    config_dict = _read_config_file(name)
  with open(name, 'w') as fd:
    yaml.dump(pillar_dict, fd, default_flow_style=False, width=1, indent=4)

  return True if config_dict else False

# def _read_config_file(config_filename: str) -> dict:
def _read_config_file(config_filename):
  config_data = None

  try:
    config_data = _read_yaml(config_filename)
  except Exception as ex:
    # print(ex)
    try:
      config_data = _read_ini(config_filename)
    except Exception as ex:
      # print(ex)
      print("Unexpected file format encountered.")

  return config_data

# def _read_yaml(config_filename: str) -> dict:
def _read_yaml(config_filename):
  import yaml

  try:
    with open(config_filename, 'r') as fd:
      yaml_to_dict = yaml.safe_load(fd)
      #print(yaml_to_dict)
      return yaml_to_dict
  except yaml.YAMLError as ex:
    # print(ex)
    msg = """
    ==================================================
    ERROR: Provided input config file not in YAML format.
    Unable to read/update provided config file.
    ==================================================
    """
    raise Exception(msg)

# def _read_ini(config_filename: str) -> dict:
def _read_ini(config_filename):
  if "2." in sys.version:
    from ConfigParser import ConfigParser, ParsingError, MissingSectionHeaderError
  else:
    from configparser import ConfigParser, ParsingError, MissingSectionHeaderError

  print("Attempting INI format")
  print("Parsing file: {0}".format(config_filename))

  ini_to_dict = None
  parser = ConfigParser(allow_no_value=True)
  try:
    parser.read(config_filename)
    ini_to_dict = parser._sections
    # with open(config_filename, 'r') as fd:
    #   ini_to_dict = parser.read_string(fd.readlines())._sections

  except MissingSectionHeaderError:
    print("ERROR: INI file {0} has no section header".format(config_filename))
    with open(config_filename, 'r') as fd:
      parser.read_string("[top]\n" + fd.read())
      ini_to_dict = parser._sections

  except ParsingError as ex:
    print(ex.message)
    msg = """
    ==================================================
    ERROR: Provided input config file not in INI format.
    Unable to read/update provided config file.
    ==================================================
    """
    raise Exception(msg)
  except Exception as ex:
    print(ex)

  print("INI file read as: {0}".format(ini_to_dict))
  return ini_to_dict

# def _read_pillar(ref_component_pillar: str) -> dict:
def _read_pillar(ref_component_pillar):
  from collections import OrderedDict
  from json import loads, dumps
  __pillar__ = getattr(sys.modules[__name__], '__pillar__')
  pillar_data = __pillar__[ref_component_pillar]
  pillar_dict = loads(dumps(dict(pillar_data)))
  return pillar_dict
