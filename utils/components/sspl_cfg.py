#!/usr/bin/env python3
import json
import os.path
import yaml

from argparse import ArgumentParser, Namespace

from .base_cfg import BaseCfg


class SSPLCfg(BaseCfg):
    __options = {}
    __cfg_path = ""


    def __init__(self, cfg_path: str=None, arg_parser: ArgumentParser=None):
        if cfg_path:
            self.__cfg_path = cfg_path
        else:
            self.__cfg_path = os.path.join(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "../..",
                    "pillar"
                ),
                "components",
                "sspl.sls"
            )

        if os.path.exists(self.__cfg_path):
            self.__load_defaults()

        if arg_parser:
            self.__setup_args(arg_parser)


    def __setup_args(self, arg_parser=None):

        if not arg_parser:
            raise Exception("__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            '--sspl-file',
            dest = 'sspl_file',
            action="store",
            help='Yaml file with sspl configs')
        arg_parser.add_argument(
            '--show-sspl-file-format',
            dest = 'show_sspl_file_format',
            action="store_true",
            help='Display Yaml file format for sspl configs')


    def __load_defaults(self):
        with open(self.__cfg_path, 'r') as fd:
            self.__options = yaml.safe_load(fd)
        # print(json.dumps(self._release_options, indent = 4))
        # TODO validations for configs.


    def __read_user_inputs(self, opt_tree: dict={}, parent: list=[]) -> dict:
        for k, v in opt_tree.items():
            if isinstance(v, dict):
                parent.append(k)
                opt_tree[k] = self.__read_user_inputs(v, parent)
            else:
                printable_parent = ']['.join(parent) if parent else ''
                opt_tree[k] = input("Enter value for [{0}][{1}] -> ({2}): ".format(printable_parent, k, v))
        
        parent.pop()
        return opt_tree


    def process_inputs(self, program_args: Namespace) -> bool:

        if program_args.interactive:
            input("\nAccepting interactive inputs for pillar/sspl.sls. Press any key to continue...")

            self.__options = self.__read_user_inputs(self.__options)

            # print(json.dumps(self._release_options, indent = 4))
            return True

        elif program_args.show_sspl_file_format:
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

        elif program_args.sspl_file:
            if not os.path.exists(program_args.sspl_file):
                raise FileNotFoundError("Error: No file exists at location sepecified by argument '--sspl-file'.")

            # Load sspl file and merge options.
            new_options = {}
            with open(program_args.sspl_file, 'r') as fd:
                new_options = yaml.safe_load(fd)
                self.__options.update(new_options)
            return True

        else:
            print("Error: No usable inputs provided.")
            return False


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
