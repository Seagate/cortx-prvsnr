#!/usr/bin/python3
import argparse
import json
import yaml

class SSPLCfg:
    __options = {}
    __cfg_path = ""


    def __init__(self, arg_parser, cfg_path):
        self.__cfg_path = cfg_path
        self._setup_args(arg_parser)
        self._load_defaults()


    def _setup_args(self, arg_parser):
        # TODO - validate for accidental override
        if not arg_parser:
            raise Exception("Class cannot be initialized without an argparse object")

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


    def _load_defaults(self):
        with open(self.__cfg_path, 'r') as fd:
            self.__options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self._release_options, indent = 4))
        # TODO validations for configs.


    def process_inputs(self, arg_parser):
        program_args = arg_parser.parse_args()

        if program_args.show_sspl_file_format:
            print(yaml.dump(self.__options, default_flow_style=False, width=1, indent=4))
            return False

        elif program_args.sspl_file:
            # Load sspl file and merge options.
            new_options = {}
            with open(program_args.sspl_file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
                self.__options.update(new_options)
            return True

        elif program_args.interactive:
            input_msg = ("Enter sspl role on this system: ({0}): ".format(
                    self.__options["sspl"]["role"]
                )
            )
            self.__options["sspl"]["role"] = (
                input(input_msg)
                or
                self.__options["sspl"]["role"]
            )
            # print(json.dumps(self._release_options, indent = 4))
            return True

        else:
            # print("ERROR: No usable inputs provided.")
            return False


    def save(self):
        with open(self.__cfg_path, 'w') as fd:
            yaml.dump(self.__options, fd, default_flow_style=False, indent=4)
