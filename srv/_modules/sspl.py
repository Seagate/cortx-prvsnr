#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

import errno
import os
import sys
import json
import salt.client
from pathlib import Path

if "2." in sys.version:
  from ConfigParser import ConfigParser, ParsingError, MissingSectionHeaderError
else:
  from configparser import ConfigParser, ParsingError, MissingSectionHeaderError
from shutil import copyfile

import commons

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call sspl.conf_update "/opt/seagate/cortx/provisioner/srv/_modules/files/samples/sspl.conf" sspl

def conf_update(  name = '/etc/sspl.conf',
                  ref_pillar = 'sspl',
                  backup = True ):
  """Update component config file.

  Args :
    name: Destination path of component config file to be updated
    ref_pillar: Reference section from pillar data for a component to be updated
    backup: Backup config file before modification as bool (Default: True)
  """
  # Check if ini_file exists
  if not os.path.exists(name):
    print("[ERROR   ] Possible error with sspl installation.")
    raise FileNotFoundError(
      errno.ENOENT,
      os.strerror(errno.ENOENT),
      name
  )

  if backup:
    copyfile(name, name + '.bak')

  pillar_dict = __pillar__[ref_pillar]

  # Read
  config_dict = _read_ini(name)

  # Update
  config_dict = commons._update_dict(config_dict, pillar_dict)
  config_dict = _inject_storage_enclosure(config_dict)

  # Write
  _write_ini(name, config_dict)

  return True


# Parse INI file and return Python dict object
def _read_ini(ini_file):
  #TODO: Future logger
  # print("Attempting INI format")
  # print("Parsing file: {0}".format(ini_file))
  
  config_dict = {}
  config_sections = []
  parser = ConfigParser(allow_no_value=True)
  
  try:
    parser.read(ini_file)
    config_sections = parser.sections()
    
  except MissingSectionHeaderError:
    print("ERROR: INI file {0} has no section header".format(ini_file))
    with open(ini_file, 'r') as fd:
      parser.read_string("[top]\n" + fd.read())
      config_sections = parser.sections()

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
    raise

  for section in config_sections:
    config_dict[section] = {}
    for key in parser.options(section):
      # If value has ',' convert it to Python list object
      if ',' in parser[section][key]:
        config_dict[section][key] = [element.strip() for element in parser[section][key].split(',')]
      else:
        config_dict[section][key] = parser[section][key]

  # print("INI file read as: {0}".format(config_dict))
  return config_dict


def _write_ini(ini_file, config_dict):
  
  parser = ConfigParser(allow_no_value=True)
  
  for k in config_dict.keys():
    parser.add_section(k)
    if isinstance(config_dict[k], dict):
      for key, value in config_dict[k].items():
        if isinstance(value, list):
          parser.set(k, key, ', '.join(value))
        else:
          parser.set(k, key, str(value))

  # Save to file
  with open(ini_file, 'w') as fd:
    parser.write(fd, space_around_delimiters=False)


def _inject_storage_enclosure(config_dict={}):
  """Inject data for storage enclosure from pillar/components/cluster.sls
  """
  storage_enclosure = __pillar__['storage_enclosure']['controller']

  if storage_enclosure['user']:
    config_dict['STORAGE_ENCLOSURE']['user'] = storage_enclosure['user']
  if storage_enclosure['secret']:
    config_dict['STORAGE_ENCLOSURE']['secret'] = storage_enclosure['secret']
  if storage_enclosure['primary_mc']['ip']:
    config_dict['STORAGE_ENCLOSURE']['primary_controller_ip'] = storage_enclosure['primary_mc']['ip']
  if storage_enclosure['primary_mc']['port']:
    config_dict['STORAGE_ENCLOSURE']['primary_controller_port'] = storage_enclosure['primary_mc']['port']
  if storage_enclosure['secondary_mc']['ip']:
    config_dict['STORAGE_ENCLOSURE']['secondary_controller_ip'] = storage_enclosure['secondary_mc']['ip']
  if storage_enclosure['secondary_mc']['port']:
    config_dict['STORAGE_ENCLOSURE']['secondary_controller_port'] = storage_enclosure['secondary_mc']['port']
  
  return config_dict


def merge_health_map_schema(source_json="/tmp/resource_health_view.json"):
  
  local = salt.client.LocalClient()
  health_map_path = __pillar__['sspl']['health_map_path']
  health_map_file = __pillar__['sspl']['health_map_file']
  
  
  data = local.cmd('*', 'file.read', [source_json])
  node1_data = json.loads(data["srvnode-1"])
  node2_data = json.loads(data["srvnode-2"])

  node1_data["cluster"]["sites"]["001"]["rack"]["001"]["nodes"].update(node2_data["cluster"]["sites"]["001"]["rack"]["001"]["nodes"])
  local.cmd('*', 'file.mkdir',[health_map_path])
  local.cmd('*', 'file.write', [ os.path.join(health_map_path, health_map_file), json.dumps(node1_data, indent=4)])

  # TODO use salt formulas, CSM suggested to have 777 permission just for hotfix
  local.cmd('*', 'cmd.run', ['chmod 777 {}'.format(os.path.join(health_map_path, health_map_file))])
  return True
