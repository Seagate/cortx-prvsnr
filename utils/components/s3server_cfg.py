#!/usr/bin/python3
import argparse
import json
import yaml

class S3ServerCfg:
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
            '--s3server-file',
            dest = 's3server_file',
            action="store",
            help='Yaml file with s3server configs'
        )
        arg_parser.add_argument(
            '--show-s3server-file-format',
            dest = 'show_s3server_file_format',
            action="store_true",
            help='Display Yaml file format for s3server configs'
        )


    def _load_defaults(self):
        with open(self.__cfg_path, 'r') as fd:
            self.__options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self.__options, indent = 4))
        # TODO validations for configs.


    def process_inputs(self, arg_parser):
        program_args = arg_parser.parse_args()

        if program_args.show_s3server_file_format:
            print(yaml.dump(self.__options, default_flow_style=False, width=1, indent=4))
            return False

        elif program_args.s3server_file:
            # Load s3server file and merge options.
            new_options = {}
            with open(program_args.s3server_file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
            self.__options.update(new_options)
            return False

        elif program_args.interactive:
            input_msg = (
                "Reuse the port for s3server? (true/false)({0}): ".format(
                    self.__options["s3server"]["reuseport"]
                )
            )
            self.__options["s3server"]["reuseport"] = (
                input(input_msg)
                or
                self.__options["s3server"]["reuseport"]
            )

            input_msg = (
                "Enter the bind address for ipv4 ({0}): ".format(
                    self.__options["s3server"]["ipv4_bind_addr"]
                )
            )
            self.__options["s3server"]["ipv4_bind_addr"] = (
                input(input_msg)
                or
                self.__options["s3server"]["ipv4_bind_addr"]
            )

            input_msg = (
                "Enter the bind address for ipv6 ({0}): ".format(
                    self.__options["s3server"]["ipv6_bind_addr"]
                )
            )
            self.__options["s3server"]["ipv6_bind_addr"] = (
                input(input_msg)
                or
                self.__options["s3server"]["ipv6_bind_addr"]
            )

            input_msg = ("Enter bind port for s3server ({0}): ".format(
                self.__options["s3server"]["bind_port"]
                )
            )
            self.__options["s3server"]["bind_port"] = (
                input(input_msg)
                or
                self.__options["s3server"]["bind_port"]
            )

            input_msg = (
                "Enter the endpoint for s3 ({0}): ".format(
                    self.__options["s3server"]["default_endpoint"]
                )
            )
            self.__options["s3server"]["default_endpoint"] = (
                input(input_msg)
                or
                self.__options["s3server"]["default_endpoint"]
            )

            input_msg = (
                "Enter the regional endpoints for s3 ({0}): ".format(
                    self.__options["s3server"]["region_endpoints"]
                )
            )
            self.__options["s3server"]["region_endpoints"] = (
                input(input_msg)
                or
                self.__options["s3server"]["region_endpoints"]
            )

            input_msg = (
                "Enter the read ahead multiple ({0}): ".format(
                    self.__options["s3server"]["read_ahead_multiple"]
                )
            )
            # TODO: Put the better input message.
            self.__options["s3server"]["read_ahead_multiple"] = (
                input(input_msg)
                or
                self.__options["s3server"]["read_ahead_multiple"]
            )

            input_msg = (
                "Do you want to enable ssl for s3 server (true/false)? ({0}): ".format(
                    self.__options["ssl"]["enable"]
                )
            )
            self.__options["ssl"]["enable"] = (
                input(input_msg)
                or
                self.__options["ssl"]["enable"]
            )

            input_msg = (
                "Do you want to enable performance stats for s3 server (0/1)? ({0}): ".format(
                    self.__options["performance_local_stats"]["enable"]
                )
            )
            self.__options["performance_local_stats"]["enable"] = (
                input(input_msg)
                or
                self.__options["performance_local_stats"]["enable"]
            )

            input_msg = (
                "Enter the logging mode for s3 server (DEBUG, INFO, WARN, ERROR, FATAL) ({0}): ".format(
                    self.__options["logging"]["mode"]
                )
            )
            self.__options["logging"]["mode"] = (
                input(input_msg)
                or
                self.__options["logging"]["mode"]
            )

            input_msg = (
                "Do you want to enable buffering during logging? ({0}): ".format(
                    self.__options["logging"]["enable_buffering"]
                )
            )
            self.__options["logging"]["enable_buffering"] = (
                input(input_msg)
                or
                self.__options["logging"]["enable_buffering"]
            )

            input_msg = (
                "Do you want to enable ssl for s3 auth server? ({0}): ".format(
                    self.__options["auth_server"]["ssl"]
                )
            )
            self.__options["auth_server"]["ssl"] = (
                input(input_msg)
                or
                self.__options["auth_server"]["ssl"]
            )

            input_msg = (
                "Enter ip address for s3 auth server (for ipv6 use following format: ipv6:::1)({0}): ".format(
                    self.__options["auth_server"]["ip_addr"]
                )
            )
            self.__options["auth_server"]["ip_addr"] = (
                input(input_msg)
                or
                self.__options["auth_server"]["ip_addr"]
            )

            input_msg = (
                "Enter the port for s3 auth server to be used for https requests ({0}): ".format(
                    self.__options["auth_server"]["port"]
                )
            )
            self.__options["auth_server"]["port"] = (
                input(input_msg)
                or
                self.__options["auth_server"]["port"]
            )

            input_msg = ("Do you want to enable the Stats feature (true/false)? ({0}): ".format(
                self.__options["statsd"]["enable"]
                )
            )
            self.__options["statsd"]["enable"] = input(input_msg) or self.__options["statsd"]["enable"]

            if self.__options["statsd"]["enable"]:
                input_msg = (
                    "Enter Statsd server IP address: ({0}): ".format(
                        self.__options["statsd"]["ip_addr"]
                    )
                )
                self.__options["statsd"]["ip_addr"] = (
                    input(input_msg)
                    or
                    self.__options["statsd"]["ip_addr"]
                )

                input_msg = (
                    "Enter Statsd server IP port ({0}): ".format(
                        self.__options["statsd"]["port"]
                    )
                )
                self.__options["statsd"]["port"] = (
                    input(input_msg)
                    or
                    self.__options["statsd"]["port"]
                )

                input_msg = (
                    "Provide the path of the yaml input file for White list of Stats metrics to be published to the backend ({0}): ".format(
                        self.__options["statsd"]["whitelisting"]
                    )
                )
                self.__options["statsd"]["whitelisting"] = (
                    input(input_msg)
                    or
                    self.__options["statsd"]["whitelisting"]
                )

            config_clovis = input(
                "Do you want to configure Clovis parameters? 'no' will set the defaults. (yes/no): "
            )
            if config_clovis:
                print ("Clovis configuration Section, stick to defaults if "
                    "you are not sure about the parameters")
                input_msg = (
                    "Enter maximum units per read/write request to clovis ({0}): ".format(
                        self.__options["clovis"]["max_units_per_request"]
                    )
                )
                self.__options["clovis"]["max_units_per_request"] = (
                    input(input_msg)
                    or
                    self.__options["clovis"]["max_units_per_request"]
                )

                input_msg = (
                    "Enter maximum no of key value pair to be fetched from a KVS index ({0}): ".format(
                        self.__options["clovis"]["max_idx_kv_fetch_count"]
                    )
                )
                # TODO: Enter beeter input message.
                self.__options["clovis"]["max_idx_kv_fetch_count"] = (
                    input(input_msg)
                    or
                    self.__options["clovis"]["max_idx_kv_fetch_count"]
                )

                input_msg = (
                    "Enter the minimum length of the 'tm' receive queue for Clovis ({0}): ".format(
                        self.__options["clovis"]["tm_recv_queue_min_len"]
                    )
                )
                self.__options["clovis"]["tm_recv_queue_min_len"] = (
                    input(input_msg)
                    or
                    self.__options["clovis"]["tm_recv_queue_min_len"]
                )

                input_msg = (
                    "Enter the maximum size of the rpc message for Clovis [{0} bytes]: ".format(
                        self.__options["clovis"]["max_rpc_msg_size"]
                    )
                )
                self.__options["clovis"]["max_rpc_msg_size"] = (
                    input(input_msg)
                    or
                    self.__options["clovis"]["max_rpc_msg_size"]
                )

                print ("Clovis memory pool configuration Section, stick to "
                    "defaults if you are not sure about the parameters")
                input_msg = (
                    "Enter array of unit sizes to create Clovis memory pools ({0}): ".format(
                        self.__options["clovis"]["memory_pool"]["unit_sizes"]
                    )
                )
                self.__options["clovis"]["memory_pool"]["unit_sizes"] = (
                    input(input_msg)
                    or
                    self.__options["clovis"]["memory_pool"]["unit_sizes"]
                )

                input_msg = (
                    "Enter the read initial buffer count ({0}): ".format(
                        self.__options["clovis"]["memory_pool"]["read_initial_buffer_count"]
                    )
                )
                # TODO: Enter better input message.
                self.__options["clovis"]["memory_pool"]["read_initial_buffer_count"] = (
                    input(input_msg)
                    or
                    self.__options["clovis"]["memory_pool"]["read_initial_buffer_count"]
                )

                input_msg = (
                    "Enter pool's expandable size in blocks (multiple of S3_CLOVIS_UNIT_SIZE) ({0}): ".format(
                        self.__options["clovis"]["memory_pool"]["read_expandable_count"]
                    )
                )
                self.__options["clovis"]["memory_pool"]["read_expandable_count"] = (
                    input(input_msg)
                    or
                    self.__options["clovis"]["memory_pool"]["read_expandable_count"]
                )

                input_msg = (
                    "Enter the maximum memory threshold for the pool in bytes (multiple of S3_CLOVIS_UNIT_SIZE) ({0}): ".format(
                        self.__options["clovis"]["memory_pool"]["read_max_threshold_in_bytes"]
                    )
                )
                self.__options["clovis"]["memory_pool"]["read_max_threshold_in_bytes"] = (
                    input(input_msg)
                    or
                    self.__options["clovis"]["memory_pool"]["read_max_threshold_in_bytes"]
                )

            config_libevent = input(
                "Do you want to configure libevent parameters? 'no' will set the defaults. (yes/no): "
            )

            if config_libevent:
                print ("Libevent configuration Section, stick to defaults if you are not sure about the parameters")
                input_msg = (
                    "Enter maximum read size for a single read operation in bytes (user should not try to read more than this value) ({0}): ".format(
                        self.__options["thirdparty"]["libevent"]["max_read_size_in_bytes"]
                    )
                )
                self.__options["thirdparty"]["libevent"]["max_read_size_in_bytes"] = (
                    input(input_msg)
                    or
                    self.__options["thirdparty"]["libevent"]["max_read_size_in_bytes"]
                )

                input_msg = (
                    "Enter Libevent pool buffer size, (in case of "
                    "S3_CLOVIS_UNIT_SIZE of size 1MB, it is recommended to "
                    "have S3_LIBEVENT_POOL_BUFFER_SIZE of size 16384) ({0}): ".format(
                        self.__options["thirdparty"]["memory_pool"]["pool_buffer_size_in_bytes"]
                    )
                )
                self.__options["thirdparty"]["memory_pool"]["pool_buffer_size_in_bytes"] = (
                    input(input_msg)
                    or
                    self.__options["thirdparty"]["memory_pool"]["pool_buffer_size_in_bytes"]
                )

                input_msg = ("Enter the initial pool size in bytes (should be multiple of S3_CLOVIS_UNIT_SIZE) ({0}):".format(
                        self.__options["thirdparty"]["memory_pool"]["initial_size_in_bytes"]
                    )
                )
                self.__options["thirdparty"]["memory_pool"]["initial_size_in_bytes"] = (
                    input(input_msg)
                    or
                    self.__options["thirdparty"]["memory_pool"]["initial_size_in_bytes"]
                )

                input_msg = (
                    "Enter pool's expandable size in bytes "
                    "(should be multiple of S3_CLOVIS_UNIT_SIZE) ({0}):".format(
                        self.__options["thirdparty"]["memory_pool"]["expandable_size_in_bytes"]
                    )
                )
                self.__options["thirdparty"]["memory_pool"]["expandable_size_in_bytes"] = (
                    input(input_msg)
                    or
                    self.__options["thirdparty"]["memory_pool"]["expandable_size_in_bytes"]
                )

                input_msg = ("Enter the maximum memory threshold for the pool in bytes "
                    "(should be multiple of S3_CLOVIS_UNIT_SIZE) ({0}):".format(
                        self.__options["thirdparty"]["memory_pool"]["max_threshold_in_bytes"]
                    )
                )
                self.__options["thirdparty"]["memory_pool"]["max_threshold_in_bytes"] = (
                    input(input_msg)
                    or
                    self.__options["thirdparty"]["memory_pool"]["max_threshold_in_bytes"]
                )
            # print(json.dumps(self.__options, indent = 4))
            return True

        else:
            # print("ERROR: No usable inputs provided.")
            return False


    def save(self):
        with open(self.__cfg_path, 'w') as fd:
            yaml.dump(self.__options, fd, default_flow_style=False, indent=4)
