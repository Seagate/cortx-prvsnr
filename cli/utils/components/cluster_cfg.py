#!/usr/bin/env python3
import json
import os.path
import yaml
from shutil import copy

from argparse import ArgumentParser, Namespace

from .base_cfg import BaseCfg


class ClusterCfg(BaseCfg):

    def __init__(self, cfg_path: str=None, arg_parser: ArgumentParser=None):

        if cfg_path:
            self._cfg_path = cfg_path
        else:
            self._cfg_path = os.path.join(
                self._pillar_path,
                "components",
                "cluster.sls"
            )

        if arg_parser:
            self.__setup_args(arg_parser)

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

        arg_parser.add_argument(
            '--load-default',
            dest = 'load_default',
            action = 'store_true',
            help = 'Reset default values to a modified YAML file'
        )


    def process_inputs(self, program_args: Namespace) -> bool:
        if program_args.interactive:
            input(
                "\nAccepting interactive inputs for pillar/cluster.sls. Press any key to continue...")
            for node in self._options["cluster"]["node_list"]:
                input_msg = ("\nEnter hostname for ees {1} ({0}): ".format(
                    self._options["cluster"][node]["hostname"], node
                )
                )
                self._options["cluster"][node]["hostname"] = (
                    input(input_msg)
                    or
                    self._options["cluster"][node]["hostname"]
                )

                input_msg = ("Is this a primary ees node? ({0}): ".format(
                    self._options["cluster"][node]["is_primary"]
                )
                )
                self._options["cluster"][node]["is_primary"] = (
                    input(input_msg)
                    or
                    self._options["cluster"][node]["is_primary"]
                )

                input_msg = ("Enter management interface name ({0}): ".format(
                    self._options["cluster"][node]["network"]["mgmt_nw"]["iface"]
                )
                )
                self._options["cluster"][node]["network"]["mgmt_nw"]["iface"] = (
                    input(input_msg)
                    or
                    self._options["cluster"][node]["network"]["mgmt_nw"]["iface"]
                )

                input_msg = ("Enter data interface name ({0}): ".format(
                    self._options["cluster"][node]["network"]["data_nw"]["iface"]
                )
                )
                self._options["cluster"][node]["network"]["data_nw"]["iface"] = (
                    input(input_msg)
                    or
                    self._options["cluster"][node]["network"]["data_nw"]["iface"]
                )

                input_msg = ("Enter the default gateway ip ({0}): ".format(
                    self._options["cluster"][node]["network"]["gateway_ip"]
                )
                )
                self._options["cluster"][node]["network"]["gateway_ip"] = (
                    input(input_msg)
                    or
                    self._options["cluster"][node]["network"]["gateway_ip"]
                )

                input_msg = ("Enter the default metadata_device ({0}): ".format(
                    self._options["cluster"][node]['storage']["metadata_device"][0]
                )
                )
                self._options["cluster"][node]['storage']["metadata_device"][0] = (
                    input(input_msg)
                    or
                    self._options["cluster"][node]['storage']["metadata_device"][0]
                )

                input_msg = ("Enter the data disk device for {1} ({0}): ".format(
                    self._options["cluster"][node]['storage']["data_devices"][0], node
                )
                )
                self._options["cluster"][node]['storage']["data_devices"][0] = (
                    input(input_msg)
                    or
                    self._options["cluster"][node]['storage']["data_devices"][0]
                )

            # Process args for node_2
            # print(json.dumps(self._options, indent = 4))
            return True

        elif program_args.show_cluster_file_format:
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

        elif program_args.cluster_file:
            if not os.path.exists(program_args.cluster_file):
                raise FileNotFoundError("Error: No file exists at location sepecified by argument '--cluster-file'.")
            # Load cluster file and merge options.
            new_options = {}
            with open(program_args.cluster_file, 'r') as fd:
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

