#!/usr/bin/python3
import argparse
import json
import yaml


class ClusterCfg:
    __options = {}
    __cfg_path = ""


    def __init__(self, arg_parser, cfg_path):
        if not arg_parser:
            raise Exception("Class cannot be initialized without an argparse object")

        self.__cfg_path = cfg_path
        self._setup_args(arg_parser)
        self._load_defaults()


    def _setup_args(self, arg_parser):
        # TODO - validate for accidental override
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


    def _load_defaults(self):
        with open(self.__cfg_path, 'r') as fd:
            self.__options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self._mero_options, indent = 4))
        # TODO validations for configs.


    def process_inputs(self, arg_parser):
        program_args = arg_parser.parse_args()

        if program_args.show_cluster_file_format:
            print(yaml.dump(self.__options, default_flow_style=False, width=1, indent=4))
            return False

        elif program_args.cluster_file:
            # Load cluster file and merge options.
            new_options = {}
            with open(program_args.cluster_file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
            self.__options.update(new_options)
            return True

        elif program_args.interactive:
            input_msg = ("Enter fqdn for ees node 1 ({0}): ".format(
                    self.__options["facts"]["node_1"]["fqdn"]
                )
            )
            self.__options["facts"]["node_1"]["fqdn"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["fqdn"]
            )

            input_msg = ("Is this a primary ees node? ({0}): ".format(
                    self.__options["facts"]["node_1"]["primary"]
                )
            )
            self.__options["facts"]["node_1"]["primary"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["primary"]
            )

            input_msg = ("Enter management interface name ({0}): ".format(
                    self.__options["facts"]["node_1"]["mgmt_if"]
                )
            )
            self.__options["facts"]["node_1"]["mgmt_if"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["mgmt_if"]
            )

            input_msg = ("Enter data interface name ({0}): ".format(
                    self.__options["facts"]["node_1"]["data_if"]
                )
            )
            self.__options["facts"]["node_1"]["data_if"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["data_if"]
            )

            input_msg = ("Enter the default gateway ip ({0}): ".format(
                    self.__options["facts"]["node_1"]["gateway_ip"]
                )
            )
            self.__options["facts"]["node_1"]["gateway_ip"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["gateway_ip"]
            )

            input_msg = ("Enter the data disk device for node_1 ({0}): ".format(
                    self.__options["facts"]["node_1"]["data_device_1"]
                )
            )
            self.__options["facts"]["node_1"]["data_device_1"] = (
                input(input_msg)
                or
                self.__options["facts"]["node_1"]["data_device_1"]
            )

            # Process args for node_2
            # print(json.dumps(self.__options, indent = 4))
            return True

        else:
            # print("ERROR: No usable inputs provided.")
            return False


    def save(self):
        with open(self.__cfg_path, 'w') as fd:
            yaml.dump(self.__options, fd, default_flow_style=False, indent=4)
