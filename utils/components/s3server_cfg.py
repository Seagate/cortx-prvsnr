import json
import yaml

class S3ServerCfg:
    _s3server_options = {}
    _cfg_path = ""

    def __init__(self, arg_parser, cfg_path):
        self._cfg_path = cfg_path
        self._setup_args(arg_parser)
        self._load_defaults()

    def _setup_args(self, arg_parser):
        # TODO - validate for accidental override
        arg_parser.add_argument('--s3server-file', action="store", help='Yaml file\
             with s3server configs')
        arg_parser.add_argument('--show-s3server-file-format', action="store_true",
                                help='Display Yaml file format for s3server configs')

    def _load_defaults(self):
        with open(self._cfg_path, 'r') as fd:
            self._s3server_options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self._s3server_options, indent = 4))
        # TODO validations for configs.

    def process_inputs(self, program_args):
        if program_args.show-s3server-file-format:
            print(self._s3server_options)
            return False
        elif program_args.s3server-file:
            # Load s3server file and merge options.
            new_options = {}
            with open(program_args.s3server-file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
            self._s3server_options.update(new_options)
            return False
        elif program_args.interactive:
            input_msg = ("Reuse the port for s3server? (true/false) "
            "(default is %s):"\
                .format(self._s3server_options["s3server"]["reuseport"]))
            self._s3ssl_options["s3server"]["reuseport"] = \
                raw_input(input_msg) or \
                    self._s3server_options["s3server"]["reuseport"]

            input_msg = ("Enter the bind address for ipv4 (default is %s):"\
                .format(self._s3ssl_options["s3server"]["ipv4_bind_addr"]))
            self._s3ssl_options["s3server"]["ipv4_bind_addr"] = \
                raw_input (input_msg) or \
                    self._s3server_options["s3server"]["ipv4_bind_addr"]

            input_msg = ("Enter the bind address for ipv6 (default is %s):"\
                .format(self._s3ssl_options["s3server"]["ipv6_bind_addr"]))
            self._s3ssl_options["s3server"]["ipv6_bind_addr"] = \
                raw_input (input_msg) or 
                self._s3server_options["s3server"]["ipv6_bind_addr"]

            input_msg = ("Enter bind port for s3server (default is %s):"\
                .format(self._s3ssl_options["s3server"]["bind_port"]))
            self._s3ssl_options["s3server"]["bind_port"] = \
                raw_input(input_msg) or \
                     self._s3server_options["s3server"]["bind_port"]

            input_msg = ("Enter the endpoint for s3 (default is %s):"\
                .format(self._s3ssl_options["s3server"]["default_endpoint"]))
            self._s3ssl_options["s3server"]["default_endpoint"] = \
                raw_input(input_msg) or \
                    self._s3server_options["s3server"]["default_endpoint"]

            input_msg = ("Enter the regional endpoints for s3 (defaults are %s):"\
                .format(self._s3ssl_options["s3server"]["region_endpoints"]))
            self._s3ssl_options["s3server"]["region_endpoints"] = \
                raw_input(input_msg) or \
                    self._s3server_options["s3server"]["region_endpoints"]

            input_msg = ("Enter the read ahead multiple (default is %s):"\
                .format(self._s3ssl_options["s3server"]["read_ahead_multiple"]))
            # TODO: Put the better input message.
            self._s3ssl_options["s3server"]["read_ahead_multiple"] = \
                raw_input(input_msg) or \
                     self._s3server_options["s3server"]["read_ahead_multiple"]

            input_msg = ("Do you want to enable ssl for s3 server "
                "(true/false)? (default is %s):"\
                .format(self._s3ssl_options["ssl"]["enable"]))
            self._s3ssl_options["ssl"]["enable"] = \
                raw_input(input_msg) or self._s3server_options["ssl"]["enable"]

            input_msg = ("Do you want to enable performance stats for s3 "
                "server (0/1)? (default is %s):"\
                .format(self._s3ssl_options["performance_local_stats"]["enable"]))
            self._s3ssl_options["performance_local_stats"]["enable"] = \
                raw_input(input_msg) or \
                    self._s3server_options["performance_local_stats"]["enable"]

            input_msg = ("Enter the logging mode for s3 server "
                "(DEBUG, INFO, WARN, ERROR, FATAL) (default is %s):"\
                .format(self._s3ssl_options["logging"]["mode"]))
            self._s3ssl_options["logging"]["mode"] = \
                raw_input(input_msg) or \
                     self._s3server_options["logging"]["mode"]

            input_msg = ("Do you want to enable buffering during logging? "
                "(default is %s):"\
                .format(self._s3ssl_options["logging"]["enable_buffering"]))
            self._s3ssl_options["logging"]["enable_buffering"] = \
                raw_input(input_msg) or \
                    self._s3server_options["logging"]["enable_buffering"]

            input_msg = ("Do you want to enable ssl for s3 auth server? "
                "(default is %s):"\
                .format(self._s3ssl_options["auth_ssl"]["ssl"]))
            self._s3ssl_options["auth_ssl"]["ssl"] = \
                raw_input(input_msg) or \
                    self._s3server_options["auth_ssl"]["ssl"]

            input_msg = ("Enter ip address for s3 auth server "
                "(default is %s, for ipv6 use following format: ipv6:::1):"\
                .format(self._s3ssl_options["auth_ssl"]["ip_addr"]))
            self._s3ssl_options["auth_ssl"]["ip_addr"] = \
                raw_input(input_msg) or \
                    self._s3server_options["auth_ssl"]["ip_addr"]

            input_msg = ("Enter the port for s3 auth server to be used for "
                "https requests (default is %s):"\
                .format(self._s3ssl_options["auth_ssl"]["port"]))
            self._s3ssl_options["auth_ssl"]["port"] = \
                raw_input(input_msg) or \
                    self._s3server_options["auth_ssl"]["port"]

            input_msg = ("Do you want to enable the Stats feature "
                "(true/false)? (default is %s):"\
                .format(self._s3ssl_options["statsd"]["enable"]))
            self._s3ssl_options["statsd"]["enable"] = raw_input(input_msg) or \
                 self._s3server_options["statsd"]["enable"]

            if self._s3ssl_options["statsd"]["enable"]: 
                input_msg = ("Enter Statsd server IP address: (default is %s):"\
                    .format(self._s3ssl_options["statsd"]["ip_addr"]))
                self._s3ssl_options["statsd"]["ip_addr"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["statsd"]["ip_addr"]

                input_msg = ("Enter Statsd server IP port (default is %s):"\
                    .format(self._s3ssl_options["statsd"]["port"]))
                self._s3ssl_options["statsd"]["port"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["statsd"]["port"]

                input_msg = ("Provide the path of the yaml input file for "
                    "White list of Stats metrics to be published to the "
                    "backend(default is %s):"\
                        .format(self._s3ssl_options["statsd"]["whitelisting"]))
                self._s3ssl_options["statsd"]["whitelisting"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["statsd"]["whitelisting"]

            config_clovis = raw_input("Do you want to configure Clovis "
                "parameters? 'no' will set the defaults. (yes/no):")
            if config_clovis:
                print ("Clovis configuration Section, stick to defaults if "
                    "you are not sure about the parameters")
                input_msg = ("Enter maximum units per read/write request to "
                    "clovis (default is %s):"\
                    .format(self._s3ssl_options["clovis"]\
                        ["max_units_per_request"]))
                self._s3ssl_options["clovis"]["max_units_per_request"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["clovis"]\
                            ["max_units_per_request"]

                input_msg = ("Enter maximum no of key value pair to be "
                    "fetched from a KVS index (default is %s):"\
                    .format(self._s3ssl_options["clovis"]\
                        ["max_idx_kv_fetch_count"]))
                # TODO: Enter beeter input message.
                self._s3ssl_options["clovis"]["max_idx_kv_fetch_count"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["clovis"]["max_idx_kv_fetch_count"]

                input_msg = ("Enter the minimum length of the 'tm' receive "
                    "queue for Clovis (default is %s):"\
                    .format(self._s3ssl_options["clovis"]["tm_recv_queue_min_len"]))
                self._s3ssl_options["clovis"]["tm_recv_queue_min_len"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["clovis"]["tm_recv_queue_min_len"]

                input_msg = ("Enter the maximum size of the rpc message for "
                    "Clovis (default is %s bytes):"\
                    .format(self._s3ssl_options["clovis"]["max_rpc_msg_size"]))
                self._s3ssl_options["clovis"]["max_rpc_msg_size"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["clovis"]["max_rpc_msg_size"]

                print ("Clovis memory pool configuration Section, stick to "
                    "defaults if you are not sure about the parameters")
                input_msg = ("Enter array of unit sizes to create Clovis "
                    "memory pools (default is %s):"\
                    .format(self._s3ssl_options["clovis"]["memory_pool"]["unit_sizes"]))
                self._s3ssl_options["clovis"]["memory_pool"]["unit_sizes"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["clovis"]["memory_pool"]["unit_sizes"]

                input_msg = ("Enter the read initial buffer count "
                    "(default is %s):"\
                    .format(self._s3ssl_options["clovis"]["memory_pool"]\
                        ["read_initial_buffer_count"]))
                # TODO: Enter better input message.
                self._s3ssl_options["clovis"]["memory_pool"]\
                    ["read_initial_buffer_count"] = raw_input(input_msg) or \
                        self._s3server_options["clovis"]["memory_pool"]\
                            ["read_initial_buffer_count"]

                input_msg = ("Enter pool's expandable size in blocks "
                    "(multiple of S3_CLOVIS_UNIT_SIZE) (default is %s):"\
                    .format(self._s3ssl_options["clovis"]["memory_pool"]\
                        ["read_expandable_count"]))
                self._s3ssl_options["clovis"]["memory_pool"]\
                    ["read_expandable_count"] = raw_input(input_msg) or \
                        self._s3server_options["clovis"]["memory_pool"]\
                            ["read_expandable_count"]

                input_msg = ("Enter the maximum memory threshold for the pool "
                    "in bytes (multiple of S3_CLOVIS_UNIT_SIZE) "
                    "(default is %s):".format(self._s3ssl_options["clovis"]\
                        ["memory_pool"]["read_max_threshold_in_bytes"]))
                self._s3ssl_options["clovis"]["memory_pool"]\
                    ["read_max_threshold_in_bytes"] = \
                    raw_input(input_msg) or \
                        self._s3server_options["clovis"]["memory_pool"]
                        ["read_max_threshold_in_bytes"]

            config_libevent = raw_input("Do you want to configure libevent "
                "parameters? 'no' will set the defaults. (yes/no):")
            if config_libevent:
                print ("Libevent configuration Section, stick to defaults if "
                    "you are not sure about the parameters")
                input_msg = ("Enter maximum read size for a single read "
                    "operation in bytes (user should not try to read more "
                    "than this value) (default is %s):"\
                    .format(self._s3ssl_options["thirdparty"]["libevent"]\
                        ["max_read_size_in_bytes"]))
                self._s3ssl_options["thirdparty"]["libevent"]\
                    ["max_read_size_in_bytes"] = raw_input(input_msg) or \
                        self._s3server_options["thirdparty"]["libevent"]\
                            ["max_read_size_in_bytes"]

                input_msg = ("Enter Libevent pool buffer size, (in case of "
                    "S3_CLOVIS_UNIT_SIZE of size 1MB, it is recommended to "
                    "have S3_LIBEVENT_POOL_BUFFER_SIZE of size 16384) "
                    "(default is %s):"\
                    .format(self._s3ssl_options["thirdparty"]["memory_pool"]\
                        ["pool_buffer_size_in_bytes"]))
                self._s3ssl_options["thirdparty"]["memory_pool"]\
                    ["pool_buffer_size_in_bytes"] = raw_input(input_msg) or \
                        self._s3server_options["thirdparty"]["memory_pool"]\
                            ["pool_buffer_size_in_bytes"]

                input_msg = ("Enter the initial pool size in bytes (should be "
                    "multiple of S3_CLOVIS_UNIT_SIZE) (default is %s):"\
                    .format(self._s3ssl_options["thirdparty"]["memory_pool"]\
                        ["initial_size_in_bytes"]))
                self._s3ssl_options["thirdparty"]["memory_pool"]\
                    ["initial_size_in_bytes"] = raw_input(input_msg) or \
                        self._s3server_options["thirdparty"]["memory_pool"]\
                            ["initial_size_in_bytes"]

                input_msg = ("Enter pool's expandable size in bytes (should "
                    "be multiple of S3_CLOVIS_UNIT_SIZE) (default is %s):"\
                    .format(self._s3ssl_options["thirdparty"]["memory_pool"]\
                        ["expandable_size_in_bytes"]))
                self._s3ssl_options["thirdparty"]["memory_pool"]\
                    ["expandable_size_in_bytes"] = raw_input(input_msg) or \
                        self._s3server_options["thirdparty"]["memory_pool"]\
                            ["expandable_size_in_bytes"]

                input_msg = ("Enter the maximum memory threshold for the "
                    "pool in bytes (should be multiple of "
                    "S3_CLOVIS_UNIT_SIZE) (default is %s):"\
                    .format(self._s3ssl_options["thirdparty"]["memory_pool"]\
                        ["max_threshold_in_bytes"]))
                self._s3ssl_options["thirdparty"]["memory_pool"]\
                    ["max_threshold_in_bytes"] = raw_input(input_msg) or \
                        self._s3server_options["thirdparty"]["memory_pool"]\
                            ["max_threshold_in_bytes"]
            # print(json.dumps(self._s3server_options, indent = 4))
            return True

    def save(self):
        with open(self._cfg_path, 'w') as fd:
            yaml.dump(self._s3server_options, fd, default_flow_style=False)