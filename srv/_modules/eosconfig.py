# def update(name: str, ref_pillar: str, backup: bool=True, file_type: str='yaml') -> bool:
def update(name, ref_pillar, backup=True, type='yaml'):
  """Update component config file.

  Args :
    name: Destination path of component config file to be updated
    ref_pillar: Reference section from pillar data for a component to be updated
    backup: Backup config file before modification as bool (Default: True)
    type: Type of config file YAML/INI (Default: True)
  """

  print (__read_config_file(name))
  return True


# def __read_config_file(config_filename: str) -> dict:
def __read_config_file(config_filename):
  config_data = None

  try:
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
    with open(config_filename) as fd:
      return yaml.safe_load(fd)
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
  import configparser

  try:
    return configparser.ConfigParser().read_file(config_filename)
  except configparser.ParsingError as ex:
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
  update(sys.argv[0], sys.argv[1])
