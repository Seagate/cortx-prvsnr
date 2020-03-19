import sys
import logging

from typing import Dict
from pathlib import Path

from .utils import load_yaml
from provisioner import param

MODULE_DIR = Path(__file__).resolve().parent
API_SPEC_PATH = MODULE_DIR / 'api_spec.yaml'
PARAMS_SPEC_PATH = MODULE_DIR / 'params_spec.yaml'

PILLAR_PATH_KEY = '_path'
PARAM_TYPE_KEY = '_type'

logger = logging.getLogger(__name__)

def process_param_spec(
    spec: Dict, parent: Path = None, path: Path = None, dest: dict = None
):
    if dest is None:
        dest = {}

    if parent is None:
        parent = Path()

    for key, value in spec.items():
        if key == PILLAR_PATH_KEY:
            path = Path(value)
        else:
            pname = str(parent / key)
            if type(value) is dict:
                _type = getattr(param, value.pop(PARAM_TYPE_KEY, 'Param'))
                if _type is param.Param:
                    process_param_spec(value, parent / key, path, dest=dest)
                else:
                    if PILLAR_PATH_KEY not in value:
                        value[PILLAR_PATH_KEY] = path
                    dest[pname] = _type.from_spec(pname, **value)
            elif type(value) is str:
                if path is None:
                    logger.error("ValueError: Pillar path for {} is unknown".format(pname))
                    #raise ValueError(
                    #    'pillar path for {} is unknown'.format(pname)
                    #)
                if pname in dest:
                    logger.error("ValueEror: Duplicate entry {}".format(pname))
                    #raise ValueError('duplicate entry {}'.format(pname))
                dest[pname] = param.Param(
                    pname, pi_path=path, pi_key=param.KeyPath(value)
                )
            else:
                logger.error("TypeError occurred {}".format(type(value)))
                #TypeError('{}'.format(type(value)))

    return dest


param_spec = process_param_spec(load_yaml(PARAMS_SPEC_PATH))
api_spec = load_yaml(API_SPEC_PATH)
