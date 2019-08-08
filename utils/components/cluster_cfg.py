#!/usr/bin/env python3
import json
import os.path
import yaml

from argparse import ArgumentParser, Namespace

from .base_cfg import BaseCfg


class ClusterCfg(BaseCfg):
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
                "cluster.sls"
            )

        if os.path.exists(self.__cfg_path):
            self.__load_defaults()

        if arg_parser:
            self.__setup_args(arg_parser)


    def __load_defaults(self):

        with open(self.__cfg_path, 'r') as fd:
            self.__options = yaml.safe_load(fd)
        # print(json.dumps(self._mero_options, indent = 4))
        # TODO validations for configs.


    def __setup_args(self, arg_parser=None):

        if not arg_parser:
            raise Exception("__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            '--cluster-file',
            dest = 'cluster_file',
            action="store",
            help='Yaml file with cluster configs'
        )

        arg_parser.add_argument(
            '--show-cluster-file-format',
            dest = 'show_cluster_file_format',
            action="store_true",
            help='Display Yaml file format for cluster configs'
        )


    def process_inputs(self, program_args: Namespace) -> bool:
        if program_args.interactive:
            input(
                "\nAccepting interactive inputs for pillar/cluster.sls. Press any key to continue...")
            for node in self.__options["facts"]:
                input_msg = ("Enter fqdn for ees {1} ({0}): ".format(
                    self.__options["facts"][node]["fqdn"], node
                )
                )
                self.__options["facts"][node]["fqdn"] = (
                    input(input_msg)
                    or
                    self.__options["facts"][node]["fqdn"]
                )

                input_msg = ("Is this a primary ees node? ({0}): ".format(
                    self.__options["facts"][node]["primary"]
                )
                )
                self.__options["facts"][node]["primary"] = (
                    input(input_msg)
                    or
                    self.__options["facts"][node]["primary"]
                )

                input_msg = ("Enter management interface name ({0}): ".format(
                    self.__options["facts"][node]["mgmt_if"]
                )
                )
                self.__options["facts"][node]["mgmt_if"] = (
                    input(input_msg)
                    or
                    self.__options["facts"][node]["mgmt_if"]
                )

                input_msg = ("Enter data interface name ({0}): ".format(
                    self.__options["facts"][node]["data_if"]
                )
                )
                self.__options["facts"][node]["data_if"] = (
                    input(input_msg)
                    or
                    self.__options["facts"][node]["data_if"]
                )

                input_msg = ("Enter the default gateway ip ({0}): ".format(
                    self.__options["facts"][node]["gateway_ip"]
                )
                )
                self.__options["facts"][node]["gateway_ip"] = (
                    input(input_msg)
                    or
                    self.__options["facts"][node]["gateway_ip"]
                )
                
                input_msg = ("Enter the default metadata_device ({0}): ".format(
                    self.__options["facts"][node]["metadata_device"]
                )
                )
                self.__options["facts"][node]["metadata_device"] = (
                    input(input_msg)
                    or
                    self.__options["facts"][node]["metadata_device"]
                )

                input_msg = ("Enter the data disk device for {1} ({0}): ".format(
                    self.__options["facts"][node]["data_device_1"], node
                )
                )
                self.__options["facts"][node]["data_device_1"] = (
                    input(input_msg)
                    or
                    self.__options["facts"][node]["data_device_1"]
                )



            # Process args for node_2
            # print(json.dumps(self.__options, indent = 4))
            return True

        elif program_args.show_cluster_file_format:
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

        elif program_args.cluster_file:
            if not os.path.exists(program_args.cluster_file):
                raise FileNotFoundError("Error: No file exists at location sepecified by argument '--cluster-file'.")

            # Load cluster file and merge options.
            new_options = {}
            with open(program_args.cluster_file, 'r') as fd:
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
