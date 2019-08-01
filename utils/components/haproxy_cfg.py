#!/usr/bin/env python3
#import json
import os.path

from argparse import ArgumentParser, Namespace
import yaml
from .base_cfg import BaseCfg


class HAProxyCfg(BaseCfg):
    __options = {}
    __cfg_path = ""

    def __init__(
            self,
            cfg_path: str = None,
            arg_parser: ArgumentParser = None):

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
                "haproxy.sls"
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
            '--haproxy-file',
            dest='haproxy_file',
            action="store",
            help='Yaml file with haproxy configs')

        arg_parser.add_argument(
            '--show-haproxy-file-format',
            dest='show_haproxy_file_format',
            action="store_true",
            help='Display Yaml file format for haproxy configs')

    def __load_defaults(self):

        with open(self.__cfg_path, 'r') as stream:
            self.__options = yaml.load(stream, Loader=yaml.FullLoader)
        # print(json.dumps(self.__options, indent = 4))
        # TODO validations for configs.

    def process_inputs(self, program_args: Namespace) -> bool:

        if program_args.interactive:
            input(
                "\nAccepting interactive inputs for pillar/haproxy.sls. \
		    Press any key to continue...")

            input_msg = (
                "Enter no of background processes for HAProxy ({0}): ".format(
                    self.__options["haproxy"]["nbproc"]))
            self.__options["haproxy"]["nbproc"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["nbproc"])

            input_msg = ("Enable ssl for frontend s3 server (true/false)({0}): ".format(
                self.__options["haproxy"]["frontend"]["s3server"]["ssl_enabled"]))
            self.__options["haproxy"]["frontend"]["s3server"]["ssl_enabled"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["frontend"]["s3server"]["ssl_enabled"])

            input_msg = ("Enable ssl for frontend s3 auth server (true/false)({0}): ".format(
                self.__options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"]))
            self.__options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"])

            input_msg = ("Enable ssl for backend s3 server (true/false)({0}): ".format(
                self.__options["haproxy"]["backend"]["s3server"]["ssl_enabled"]))
            self.__options["haproxy"]["backend"]["s3server"]["ssl_enabled"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["backend"]["s3server"]["ssl_enabled"])

            input_msg = ("Enable ssl for backend s3 auth server (true/false)({0}): ".format(
                self.__options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"]))
            self.__options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"] = (
                input(input_msg)
                or
                self.__options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"])
            # print(json.dumps(self.__options, indent = 4))
            return True

        elif program_args.show_haproxy_file_format:
            print(yaml.dump(self.__options,
                            default_flow_style=False, width=1, indent=4))
            return False

        elif program_args.haproxy_file:
            if not os.path.exists(program_args.haproxy_file):
                raise FileNotFoundError(
                    "Error: No file exists at location sepecified by argument '--haproxy-file'.")

            # Load haproxy file and merge options.
            new_options = {}

            with open(program_args.haproxy_file, 'r') as stream:
                new_options = yaml.load(stream, Loader=yaml.FullLoader)
                self.__options.update(new_options)
            return True

        else:
            print("Error: No usable inputs provided.")
            return False

    def save(self):
        with open(self.__cfg_path, 'w') as stream:
            yaml.dump(
                self.__options,
                stream,
                default_flow_style=False,
                indent=4)

    def validate(self, schema_dict: dict, pillar_dict: dict) -> bool:
        pass
