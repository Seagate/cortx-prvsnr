import os.path
import re
#import sys

from shutil import copyfile

# How to test:
# $ salt-call saltutil.clear_cache
# $ salt-call saltutil.sync_modules && salt-call eoscore.conf_update "/etc/sysconfig/mero" eoscore


# def _read_pillar(ref_component_pillar: str) -> dict:
def _read_pillar(ref_component_pillar):
    return __pillar__[ref_component_pillar]


# def update(name: str, ref_pillar: str, type: str=None, backup: bool=True) -> bool:
def conf_update(name='/etc/sysconfig/mero', ref_pillar='eoscore', type=None, backup=True):
    """Update component config file.

    Args :
      name: Destination path of component config file to be updated
      ref_pillar: Reference section from pillar data for a component to be updated
      type: Type of config file YAML/INI
      backup: Backup config file before modification as bool (Default: True)
    """

    name = name if name else '/etc/sysconfig/mero'
    ref_pillar = ref_pillar if ref_pillar else 'eoscore'

    if not os.path.exists(name):
        print("ERROR: EOSCore config file {0} doesn't exist.".format(name))
        return False

    pillar_data = _read_pillar(ref_pillar)
    # print("Pillar data: {0}".format(pillar_data))

    if backup:
        copyfile(name, name + '.bak')

    with open(name, 'r+') as stream:
        file_contents = stream.read()
        for key, value in pillar_data.items():
            file_contents = re.sub(
                r'(?<={0}=).+'.format(key), str(value), file_contents)
            # for line in file_contents:
            #   if k in line:
            #     file_contents = re.sub(r'(?<=MERO_M0D_BELOG_SIZE=).+', v, file_contents)
        stream.seek(0)
        stream.write(file_contents)

    return True
