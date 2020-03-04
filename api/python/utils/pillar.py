import os
import yaml
import shutil
import salt.client

class Pillar(object):
    __options = dict()
    __pillar_path = os.path.join(
        '/',
        'opt',
        'seagate',
        'eos-prvsnr',
        "pillar"
    )

    def __init__(self, pillar: str=None):
        if not os.path.exists(self.__pillar_path):
            if os.path.exists(os.path.join('/','opt', 'seagate', 'eos-prvsnr', "pillar")):
                self.__pillar_path = os.path.join('/','opt', 'seagate', 'eos-prvsnr', "pillar")
            else:
                raise Exception("ERROR: eos-prvsnr installation is missing in: /opt/seagate/eos-prvsnr")
        #Path to pillar file
        self.__pillar_path = os.path.join(self.__pillar_path, 'components', 'system.sls')

    def __enter__(self):
        self.__load_defaults()
        return self


    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__save()


    def __load_defaults(self):
        #Parse the pillar document in a stream
        with open(self.__pillar_path, 'r') as fd:
            self.__options = yaml.safe_load(fd)


    def __backup_pillar(self):
        #Take backup of pillar file
        shutil.copy(self.__pillar_path, self.__pillar_path + ".bak")


    def __save(self):
        self.__backup_pillar()
        #Serialize a object into a YAML stream
        with open(self.__pillar_path, 'w') as fd:
            yaml.safe_dump(
                self.__options,
                stream=fd,
                default_flow_style=False,
                canonical=False,
                width=1,
                indent=4
            )
        prvsnr_client = salt.client.LocalClient()
        #Refresh pillar data after updation
        ret_val = prvsnr_client.cmd('*', 'saltutil.refresh_pillar')
        for val in ret_val.values():
            if not val:
                raise Exception("ERROR: NTP config update failed.")



    @property
    def pillar_data(self):
        return self.__options


    @pillar_data.setter
    def pillar_data(self, pillar_data: dict):
        self.__options.update(pillar_data)
