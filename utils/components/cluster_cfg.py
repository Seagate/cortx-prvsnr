#!/usr/bin/env python3
#import json
import os.path

from argparse import ArgumentParser, Namespace
import yaml
from .base_cfg import BaseCfg


class ClusterCfg(BaseCfg):
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
                "cluster.sls"
            )

        if os.path.exists(self.__cfg_path):
            self.__load_defaults()

        if arg_parser:
            self.__setup_args(arg_parser)

    def __load_defaults(self):

        with open(self.__cfg_path, 'r') as stream:
            self.__options = yaml.load(stream, Loader=yaml.FullLoader)
        # print(json.dumps(self._mero_options, indent = 4))
        # TODO validations for configs.

    def __setup_args(self, arg_parser=None):

        if not arg_parser:
            raise Exception(
                "__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            '--cluster-file',
            dest='cluster_file',
            action="store",
            help='Yaml file with cluster configs'
        )

        arg_parser.add_argument(
            '--show-cluster-file-format',
            dest='show_cluster_file_format',
            action="store_true",
            help='Display Yaml file format for cluster configs'
        )

    def process_inputs(self, program_args: Namespace) -> bool:

        if program_args.interactive:
            input(
                "\nAccepting interactive inputs for pillar/cluster.sls. \
		    Press any key to continue...")

            input_msg = ("Enter fqdn for ees node 1 ({0}): ".format(
                self.__options["facts"]["node_1"]["fqdn"]))
            self.__options["facts"]["node_1"]["fqdn"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["fqdn"])

            input_msg = ("Is this a primary ees node? ({0}): ".format(
                self.__options["facts"]["node_1"]["primary"]))
            self.__options["facts"]["node_1"]["primary"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["primary"])

            input_msg = ("Enter management interface name ({0}): ".format(
                self.__options["facts"]["node_1"]["mgmt_if"]))
            self.__options["facts"]["node_1"]["mgmt_if"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["mgmt_if"])

            input_msg = ("Enter data interface name ({0}): ".format(
                self.__options["facts"]["node_1"]["data_if"]))
            self.__options["facts"]["node_1"]["data_if"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["data_if"])

            input_msg = ("Enter the default gateway ip ({0}): ".format(
                self.__options["facts"]["node_1"]["gateway_ip"]))
            self.__options["facts"]["node_1"]["gateway_ip"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["gateway_ip"])

            input_msg = ("Enter the data disk device for node_1 ({0}): ".format(
                self.__options["facts"]["node_1"]["data_device_1"]))
            self.__options["facts"]["node_1"]["data_device_1"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["data_device_1"])

            # Process args for node_2
            # print(json.dumps(self.__options, indent = 4))
            return True

        elif program_args.show_cluster_file_format:
            print(yaml.dump(self.__options,
                            default_flow_style=False, width=1, indent=4))
            return False

        elif program_args.cluster_file:
            if not os.path.exists(program_args.cluster_file):
                raise FileNotFoundError(
                    "Error: No file exists at location sepecified by argument '--cluster-file'.")

            # Load cluster file and merge options.
            new_options = {}
            with open(program_args.cluster_file, 'r') as stream:
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
