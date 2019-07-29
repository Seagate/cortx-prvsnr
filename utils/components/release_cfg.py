#!/usr/bin/python3
#import json
import os.path
#import sys

from argparse import ArgumentParser, Namespace
import yaml
from .base_cfg import BaseCfg


class ReleaseCfg(BaseCfg):
    __options = {}
    __cfg_path = ""

    def __init__(self, cfg_path: str = None, arg_parser: ArgumentParser = None):

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
                "release.sls"
            )

        if os.path.exists(self.__cfg_path):
            self.__load_defaults()

        if arg_parser:
            self.__setup_args(arg_parser)

    def __setup_args(self, arg_parser=None):

        if not arg_parser:
            raise Exception(
                "__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            '--release',
            metavar='<ees1.0.0-PI.1-sprintX>',
            help='Release version as required in CI repo, e.g. EES_Sprint1'
        )

        arg_parser.add_argument(
            '--release-file',
            dest='release_file',
            metavar='<my_release.yaml>',
            action="store",
            help='Yaml file with release configs'
        )

        arg_parser.add_argument(
            '--show-release-file-format',
            dest='show_release_file_format',
            action="store_true",
            help='Display Yaml file format for release configs'
        )

    def __load_defaults(self):

        with open(self.__cfg_path, 'r') as stream:
            self.__options = yaml.load(stream, Loader=yaml.FullLoader)
        # print(json.dumps(self.__options, indent = 4))
        # TODO validations for configs.

    def process_inputs(self, program_args: Namespace) -> bool:

        if program_args.interactive:
            input(
                "\nAccepting interactive inputs for pillar/release.sls. \
		    Press any key to continue...")

            input_msg = ("Enter target eos release version ({0}): ".format(
                self.__options["eos_release"]["target_build"]))
            self.__options["eos_release"]["target_build"] = (
                input(input_msg)
                or
                self.__options["eos_release"]["target_build"])
            return True

        elif program_args.show_release_file_format:
            print(yaml.dump(self.__options,
                            default_flow_style=False, width=1, indent=4))
            return False

        elif program_args.release:
            self.__options["eos_release"]["target_build"] = program_args.release
            # print(json.dumps(self.__options, indent = 4))
            return True

        elif program_args.release_file:
            if not os.path.exists(program_args.release_file):
                raise FileNotFoundError(
                    "Error: No file exists at location sepecified by argument '--release-file'.")

            # Load release file and merge options.
            new_options = {}
            with open(program_args.release_file, 'r') as stream:
                new_options = yaml.load(stream, Loader=yaml.FullLoader)
                self.__options.update(new_options)
            return True

        else:
            print("Error: No usable inputs provided.")
            return False

    def save(self):
        with open(self.__cfg_path, 'w') as stream:
            yaml.dump(self.__options, stream, default_flow_style=False, indent=4)

    def validate(self, schema_dict: dict, pillar_dict: dict) -> bool:
        pass
