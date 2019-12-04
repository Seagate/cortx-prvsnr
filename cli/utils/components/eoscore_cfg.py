#!/usr/bin/env python3
import json
import os.path
import yaml
from shutil import copy

from argparse import ArgumentParser, Namespace

from .base_cfg import BaseCfg


class EOSCoreCfg(BaseCfg):
    __options = {}
    __cfg_path = ""


    def __init__(self, cfg_path: str=None, arg_parser: ArgumentParser=None):
        if cfg_path:
            self.__cfg_path = cfg_path
        else:
            self.__cfg_path = os.path.join(
                self._pillar_path,
                "components",
                "eoscore.sls"
            )

        if os.path.exists(self.__cfg_path):
            self.__load_defaults()

        if arg_parser:
            self.__setup_args(arg_parser)


    def __setup_args(self, arg_parser=None) -> bool:

        if not arg_parser:
            raise Exception("__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            '--eoscore-file',
            dest = 'eoscore_file',
            action="store",
            help='Yaml file with eoscore configs')

        arg_parser.add_argument(
            '--show-eoscore-file-format',
            dest = 'show_eoscore_file_format',
            action="store_true",
            help='Display Yaml file format for eoscore configs')

        arg_parser.add_argument(
            '--load-default',
            dest = 'load_default',
            action = 'store_true',
            help = 'Reset default values to a modified YAML file'
        )


    def __load_defaults(self):

        with open(self.__cfg_path, 'r') as fd:
            self.__options = yaml.safe_load(fd)
            # print(json.dumps(self._release_options, indent = 4))
            # TODO validations for configs.


    def process_inputs(self, program_args: Namespace) -> bool:

        if program_args.interactive:
            input("\nAccepting interactive inputs for pillar/eoscore.sls. Press any key to continue...")

            input_msg = ("Enter Maximum RPC message size to be used for eoscore daemon: ({0}):".format(
                    self.__options["eoscore"]["MERO_M0D_MAX_RPC_MSG_SIZE"]
                )
            )
            self.__options["eoscore"]["MERO_M0D_MAX_RPC_MSG_SIZE"] = (
                input(input_msg)
                or
                self.__options["eoscore"]["MERO_M0D_MAX_RPC_MSG_SIZE"]
            )

            input_msg = ("Enter Maximum BE log size to be used for eoscore daemon: ({0}):".format(
                    self.__options["eoscore"]["MERO_M0D_BELOG_SIZE"]
                )
            )
            self.__options["eoscore"]["MERO_M0D_BELOG_SIZE"] = (
                input(input_msg)
                or
                self.__options["eoscore"]["MERO_M0D_BELOG_SIZE"]
            )

            input_msg = ("Enter Maximum BE segment size to be used for eoscore daemon: ({0}):".format(
                    self.__options["eoscore"]["MERO_M0D_IOS_BESEG_SIZE"]
                )
            )
            self.__options["eoscore"]["MERO_M0D_IOS_BESEG_SIZE"] = (
                input(input_msg)
                or
                self.__options["eoscore"]["MERO_M0D_IOS_BESEG_SIZE"]
            )

            # print(json.dumps(self._options, indent = 4))
            return True

        elif program_args.show_eoscore_file_format:
            print(
                yaml.safe_dump(
                    self.__options,
                    stream=None,
                    default_flow_style=False,
                    canonical=False,
                    width=1,
                    indent=4
                )
            )
            return False

        elif program_args.eoscore_file:
            if not os.path.exists(program_args.eoscore_file):
                raise FileNotFoundError("Error: No file exists at location sepecified by argument '--eoscore-file'.")

            # Load eoscore file and merge options.
            new_options = {}
            with open(program_args.eoscore_file, 'r') as fd:
                new_options = yaml.safe_load(fd)
                self.__options.update(new_options)
            return True

        elif program_args.load_default:
            if os.path.exists(self.__cfg_path+".bak"):
                copy(self.__cfg_path+".bak",self.__cfg_path)
            else:
                print("Error: No Backup File exists ")
            return False
        else:
            print("Error: No usable inputs provided.")
            return False

    def pillar_backup(func):
        def backup(*args):
            copy(args[0].__cfg_path,args[0].__cfg_path+".bak")
            return func(*args)
        return backup


    @pillar_backup
    def save(self):
        with open(self.__cfg_path, 'w') as fd:
            yaml.safe_dump(
                self.__options,
                stream=fd,
                default_flow_style=False,
                canonical=False,
                width=1,
                indent=4
            )


    def validate(self, schema_dict: dict, pillar_dict: dict) -> bool:
        pass
