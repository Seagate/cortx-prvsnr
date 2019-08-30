import errno
import os
import sys

if "2." in sys.version:
  from ConfigParser import ConfigParser, ParsingError, MissingSectionHeaderError
else:
  from configparser import ConfigParser, ParsingError, MissingSectionHeaderError
from shutil import copyfile

import commons

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call sspl.conf_update "/opt/seagate/ees-prvsnr/srv/_modules/files/samples/sspl.conf" sspl

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
  config_dict = _read_ini(name)
  config_dict = commons._update_dict(config_dict, pillar_dict)
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
    parser.write(fd)
