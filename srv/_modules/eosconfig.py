import sys

# def update(name: str, ref_pillar: str, backup: bool=True, file_type: str='yaml') -> bool:
def update(name, ref_pillar, type=None, backup=True):
  """Update component config file.

  Args :
    name: Destination path of component config file to be updated
    ref_pillar: Reference section from pillar data for a component to be updated
    type: Type of config file YAML/INI
    backup: Backup config file before modification as bool (Default: True)
  """

  if 'YAML'.__eq__(str(type).upper()):
    print(__read_yaml(name))
  elif 'INI'.__eq__(str(type).upper()):
    print(__read_ini(name))
  else:
    print(__read_config_file(name))

  return True


# def __read_config_file(config_filename: str) -> dict:
def __read_config_file(config_filename):
  config_data = None

  try:
    print("Attempting YAML format")
    config_data = __read_yaml(config_filename)
  except Exception as e:
    print(e)
    print("Attempting INI format")
    try:
      config_data = __read_ini(config_filename)
    except Exception as e:
      print(e)

  return config_data


# def __read_yaml(config_filename: str) -> dict:
def __read_yaml(config_filename):
  import yaml

  try:
    with open(config_filename, 'r') as fd:
      yaml_to_dict = yaml.safe_load(fd)
      print(yaml_to_dict)
      return yaml_to_dict
  except yaml.YAMLError as ex:
    print(ex)
    msg = """
    ==================================================
    ERROR: Provided input config file not in YAML format.
    Unable to read/update provided config file.
    ==================================================
    """
    raise Exception(msg)


# def __read_ini(config_filename: str) -> dict:
def __read_ini(config_filename):
  if "2." in sys.version:
    from ConfigParser import ConfigParser, ParsingError
  else:
    from configparser import ConfigParser, ParsingError

  try:
    cp = ConfigParser()
    ini_to_dict = cp.read([config_filename])
    print(ini_to_dict)
    return ini_to_dict
  except ParsingError as ex:
    print(ex.message)
    msg = """
    ==================================================
    ERROR: Provided input config file not in INI format.
    Unable to read/update provided config file.
    ==================================================
    """
    raise Exception(msg)


# def __read_pillar(ref_component_pillar: str) -> dict:
def __read_pillar(ref_component_pillar):
  pass


if __name__ == "__main__":
  import sys
  update(sys.argv[1], sys.argv[2])
