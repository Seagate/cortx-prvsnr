#!/usr/bin/python3
import json
import os.path
import yaml
from shutil import copy

from argparse import ArgumentParser, Namespace

from .base_cfg import BaseCfg


class S3ClientCfg(BaseCfg):

    def __init__(self, cfg_path: str=None, arg_parser: ArgumentParser=None):

        if cfg_path:
            self._cfg_path = cfg_path
        else:
            self._cfg_path = os.path.join(
                self._pillar_path,
                "components",
                "s3client.sls"
            )

        if arg_parser:
            self.__setup_args(arg_parser)


    def __setup_args(self, arg_parser=None):

        if not arg_parser:
            raise Exception("__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            '--s3client-file',
            dest = 's3client_file',
            action="store",
            help='Yaml file with s3client configs'
        )

        arg_parser.add_argument(
            '--show-s3client-file-format',
            dest = 'show_s3client_file_format',
            action="store_true",
            help='Display Yaml file format for s3client configs'
        )

        arg_parser.add_argument(
            '--load-default',
            dest = 'load_default',
            action = 'store_true',
            help = 'Reset default values to a modified YAML file'
        )

    def process_inputs(self, program_args: Namespace) -> bool:

        if program_args.interactive:
            input("\nAccepting interactive inputs for pillar/s3client.sls. Press any key to continue...")

            input_msg = ("S3Server FQDN ({0}): ".format(
                    self._options["s3client"]["s3server"]["fqdn"]
                )
            )
            self._options["s3client"]["s3server"]["fqdn"] = (
                input(input_msg)
                or
                self._options["s3client"]["s3server"]["fqdn"]
            )

            input_msg = ("S3Server IP ({0}): ".format(
                    self._options["s3client"]["s3server"]["ip"]
                )
            )
            self._options["s3client"]["s3server"]["ip"] = (
                input(input_msg)
                or
                self._options["s3client"]["s3server"]["ip"]
            )

            input_msg = ("S3 Access Key: ")
            self._options["s3client"]["access_key"] = (
                input(input_msg)
                or
                self._options["s3client"]["access_key"]
            )

            input_msg = ("S3 Secret Key: ")
            self._options["s3client"]["secret_key"] = (
                input(input_msg)
                or
                self._options["s3client"]["secret_key"]
            )

            input_msg = ("Region ({0}): ".format(
                    self._options["s3client"]["region"]
                )
            )
            self._options["s3client"]["region"] = (
                input(input_msg)
                or
                self._options["s3client"]["region"]
            )

            input_msg = ("Output format ({0}): ".format(
                    self._options["s3client"]["output"]
                )
            )
            self._options["s3client"]["output"] = (
                input(input_msg)
                or
                self._options["s3client"]["output"]
            )

            input_msg = ("S3 Endpoint ({0}): ".format(
                    self._options["s3client"]["s3endpoint"]
                )
            )
            self._options["s3client"]["s3endpoint"] = (
                input(input_msg)
                or
                self._options["s3client"]["s3endpoint"]
            )
            # print(json.dumps(self._options, indent = 4))
            return True

        elif program_args.show_s3client_file_format:
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

        elif program_args.s3client_file:
            if not os.path.exists(program_args.s3client_file):
                raise FileNotFoundError("Error: No file exists at location sepecified by argument '--s3client-file'.")

            # Load s3server file and merge options.
            new_options = {}
            with open(program_args.s3client_file, 'r') as fd:
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
