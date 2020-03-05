#!/usr/bin/python3
import json
import os.path
import sys
import yaml
from shutil import copy

from argparse import ArgumentParser, Namespace

from .base_cfg import BaseCfg


class ReleaseCfg(BaseCfg):

    def __init__(self, cfg_path: str=None, arg_parser: ArgumentParser=None):

        if cfg_path:
            self._cfg_path = cfg_path
        else:
            self._cfg_path = os.path.join(
                self._pillar_path,
                "components",
                "release.sls"
            )

        if arg_parser:
            self.__setup_args(arg_parser)


    def __setup_args(self, arg_parser=None):

        if not arg_parser:
            raise Exception("__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            '--release',
            metavar='<ees1.0.0-PI.1-sprintX>',
            help='Release version as required in CI repo, e.g. EES_Sprint1'
        )

        arg_parser.add_argument(
            '--release-file',
            dest = 'release_file',
            metavar='<my_release.yaml>',
            action="store",
            help='Yaml file with release configs'
        )

        arg_parser.add_argument(
            '--show-release-file-format',
            dest = 'show_release_file_format',
            action="store_true",
            help='Display Yaml file format for release configs'
        )

        arg_parser.add_argument(
            '--load-default',
            dest = 'load_default',
            action = 'store_true',
            help = 'Reset default values to a modified YAML file'
        )

    def process_inputs(self, program_args: Namespace) -> bool:

        if program_args.interactive:
            input("\nAccepting interactive inputs for pillar/release.sls. Press any key to continue...")

            input_msg = ("Enter target eos release version ({0}): ".format(
                    self._options["eos_release"]["target_build"]
                )
            )
            self._options["eos_release"]["target_build"] = (
                input(input_msg)
                or
                self._options["eos_release"]["target_build"]
            )
            return True


        elif program_args.show_release_file_format:
            print(
                yaml.safe_dump(
                    self._options,
                    stream=None,
                    default_flow_style=False,
                    canonical=False,
                    width=1,
                    indent=4
                )
            )
            return False

        elif program_args.release:
            self._options["eos_release"]["target_build"] = program_args.release
            # print(json.dumps(self._options, indent = 4))
            return True

        elif program_args.release_file:
            if not os.path.exists(program_args.release_file):
                raise FileNotFoundError("Error: No file exists at location sepecified by argument '--release-file'.")

            # Load release file and merge options.
            new_options = {}
            with open(program_args.release_file, 'r') as fd:
                new_options = yaml.safe_load(fd)
                self._options.update(new_options)
            return True

        elif program_args.load_default:
            if os.path.exists(self._cfg_path+".bak"):
                copy(self._cfg_path+".bak",self._cfg_path)
            else:
                print("Error: No Backup File exists ")
            return False
        else:
            print("Error: No usable inputs provided.")
            return False

    def pillar_backup(func):
        def backup(*args):
            copy(args[0]._cfg_path,args[0]._cfg_path+".bak")
            return func(*args)
        return backup


    @pillar_backup
    def save(self):
        with open(self._cfg_path, 'w') as fd:
            yaml.safe_dump(
                self._options,
                stream=fd,
                default_flow_style=False,
                canonical=False,
                width=1,
                indent=4
            )


    def validate(self, schema_dict: dict, pillar_dict: dict) -> bool:
        pass
