#!/usr/bin/python3

# Encrypts passwords in pillar in place
import argparse
import os
import salt.client
import sys
import yaml
import logging

from shutil import copy

from eos.utils.security.cipher import Cipher, CipherInvalidToken

logger = logging.getLogger(__name__)
handler = logging.FileHandler('/opt/seagate/cortx/eos-prvsnr/log/pillar-encrypt.log', mode='w')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("[%(levelname)s - %(asctime)s]: %(message)s"))
logger.addHandler(handler)

class PillarEncrypt(object):

    __options = {}
    __root_path = os.path.join('/', 'opt', 'seagate', 'eos-prvsnr')

    __pillar_path = os.path.join(
        __root_path,
        "pillar",
        "components"
    )


    def __load(self, sls_file):
        # No need to check file before open as we know, it exists.
        with open(sls_file, 'r') as fd:
            self.__options.update(yaml.safe_load(fd))


    def __save(self, sls_file):
        with open(sls_file, 'w') as fd:
            yaml.safe_dump(
                self.__options,
                stream=fd,
                default_flow_style=False,
                canonical=False,
                width=1,
                indent=4
            )
        self.__options.clear()


    def __encrypt_all_password_field(self, data, cipher_key):
        for key, val in data.items():
            if isinstance(val, dict):
                data[key] = self.__encrypt_all_password_field(val, cipher_key)
            else:
                if ("secret" in key) and (val):
                    try:
                        (Cipher.decrypt(cipher_key, val.encode("utf-8"))).decode("utf-8")
                        data[key] = val
                        # Already encrypted, do nothing
                    except CipherInvalidToken:
                        data[key] = str(Cipher.encrypt(cipher_key, bytes(val,'utf8')),'utf-8')
        return data


    def __decrypt_all_password_field(self, data, cipher_key):
        for key, val in data.items():
            if isinstance(val, dict):
                data[key] = self.__decrypt_all_password_field(val, cipher_key)
            else:
                if ("secret" in key) and (val):
                    try:
                        data[key] = (Cipher.decrypt(cipher_key, val.encode("utf-8"))).decode("utf-8")
                    except CipherInvalidToken:
                        # Already decrypted, nothing to do
                        data[key] = val
                    
        return data


    def execute(self):
        arg_parser = argparse.ArgumentParser(
            description='Encrypt passwords in Salt Pillar data.'
        )
        arg_parser.add_argument(
            '-d', '--decrypt',
            help='Decrypt passwords in provisioning data.',
            action="store_true"
        )
        flag = arg_parser.parse_args()

        cluster_id = salt.client.Caller().function('grains.get', 'cluster_id')
        
        with os.scandir(self.__pillar_path) as dir_elements:
            for file_element.is_file() and file_element.name.endswith('.sls'):
                if file_element.is_file():
                    # print(f"SLS file: {file_element.name}")
                    sls_file = os.path.join(
                        self.__pillar_path,
                        f"{file_element.name}"
                    )

                    self.__load(sls_file)
        
                    cipher_key = Cipher.generate_key(
                                    cluster_id,
                                    list(self.__options.keys())[0]
                                )

                    if flag.decrypt:
                        logger.info("Decryption started for {}".format(file_element.name))
                        self.__options.update(
                            self.__decrypt_all_password_field(
                                self.__options,
                                cipher_key
                            )
                        )
                    else:
                        logger.info("Encryption started for {}".format(file_element.name))
                        self.__options.update(
                            self.__encrypt_all_password_field(
                                self.__options,
                                cipher_key
                            )
                        )

                    self.__save(sls_file)
                    
        logger.info("DONE")


if __name__ == "__main__":
    try:
        PillarEncrypt().execute()
    except KeyboardInterrupt as e:
        print("\n\nWARNING: User aborted command. Partial data save/corruption might occur. It is advised to re-run the command.")
        sys.exit(1)
