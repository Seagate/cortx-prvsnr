#!/usr/bin/env python3
import json
import yaml

from argparse import ArgumentParser

from .base_cfg import BaseCfg


class HAProxyCfg(BaseCfg):
    __options = {}
    __cfg_path = ""


    def __init__(self, arg_parser, cfg_path):
        if not arg_parser:
            raise Exception("Class cannot be initialized without an argparse object")

        self.__cfg_path = cfg_path
        self.__setup_args(arg_parser)
        self.__load_defaults()


    def __setup_args(self, arg_parser):
        # TODO - validate for accidental override
        arg_parser.add_argument(
            '--haproxy-file',
            dest = 'haproxy_file',
            action="store",
            help='Yaml file with haproxy configs')

        arg_parser.add_argument(
            '--show-haproxy-file-format',
            dest = 'show_haproxy_file_format',
            action="store_true",
            help='Display Yaml file format for haproxy configs')


    def __load_defaults(self):
        with open(self.__cfg_path, 'r') as fd:
            self.__options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self.__options, indent = 4))
        # TODO validations for configs.


    def process_inputs(self, arg_parser: ArgumentParser) -> bool:
        program_args = arg_parser.parse_args()

        if program_args.show_haproxy_file_format:
            print(yaml.dump(self.__options, default_flow_style=False, width=1, indent=4))
            return False

        elif program_args.haproxy_file:
            # Load haproxy file and merge options.
            new_options = {}

            with open(program_args.haproxy_file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
                self.__options.update(new_options)
            return True

        elif program_args.interactive:
            input_msg = ("Enter no of background processes for HAProxy ({0}): ".format(
                    self.__options["haproxy"]["nbproc"]
                )
            )
            self.__options["haproxy"]["nbproc"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["nbproc"]
            )

            input_msg = ("Enable ssl for frontend s3 server (true/false)({0}): ".format(
                    self.__options["haproxy"]["frontend"]["s3server"]["ssl_enabled"]
                )
            )
            self.__options["haproxy"]["frontend"]["s3server"]["ssl_enabled"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["frontend"]["s3server"]["ssl_enabled"]
            )

            input_msg = ("Enable ssl for frontend s3 auth server (true/false)({0}): ".format(
                    self.__options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"]
                )
            )
            self.__options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"]
            )

            input_msg = ("Enable ssl for backend s3 server (true/false)({0}): ".format(
                    self.__options["haproxy"]["backend"]["s3server"]["ssl_enabled"]
                )
            )
            self.__options["haproxy"]["backend"]["s3server"]["ssl_enabled"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["backend"]["s3server"]["ssl_enabled"]
            )

            input_msg = ("Enable ssl for backend s3 auth server (true/false)({0}): ".format(
                    self.__options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"]
                )
            )
            self.__options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"]
            )
            # print(json.dumps(self.__options, indent = 4))
            return True

        else:
            # print("WARNING: No usable inputs provided.")
            return False


    def save(self):
        with open(self.__cfg_path, 'w') as fd:
            yaml.dump(self.__options, fd, default_flow_style=False, indent=4)


    def load(self, yaml_file):
        pass


    def validate(self, yaml_string) -> bool:
        pass
