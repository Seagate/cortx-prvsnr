
def _update_dict(source_dict = {}, reference_dict = {}):
  """ Update config file dict based on pillar dict

  Args:
    source_dict: Dictionary built from component config file.
    reference_dict: Dictionary obtained from component pillar.
  """
  if not (source_dict or reference_dict):
    raise Exception("[ERROR   ]: Empty args passed to _modules/commons.py::_config_update")
  
  for key in list(source_dict.keys()):
    if key in reference_dict:
      if isinstance(source_dict[key], dict):
        _update_dict(source_dict[key], reference_dict[key])
      else:
        source_dict[key] = reference_dict[key]
  
  return source_dict
  