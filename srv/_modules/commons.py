
def _update_dict(source_dict = {}, reference_dict = {}):
  """ Update config file dict based on pillar dict

  Args:
    source_dict: Dictionary built from component config file.
    reference_dict: Dictionary obtained from component pillar.
  """
  if not (isinstance(source_dict, dict)or isinstance(reference_dict, dict) ):
    raise Exception("[ERROR   ]: non dict args passed to _modules/commons.py::_config_update")
  
  for key in list(reference_dict.keys()):
    if( key in source_dict and isinstance(source_dict[key], dict) and
         isinstance(reference_dict[key], dict)):
        _update_dict(source_dict[key], reference_dict[key])
    else:
        source_dict[key] = reference_dict[key]
  