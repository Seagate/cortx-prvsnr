#!/usr/bin/python3
import argparse
import json
import yaml


class HAProxyCfg:
    _haproxy_options = {}
    _cfg_path = ""


    def __init__(self, arg_parser, cfg_path):
        if not arg_parser:
            raise Exception("Class cannot be initialized without an argparse object")

        self._cfg_path = cfg_path
        self._setup_args(arg_parser)
        self._load_defaults()


    def _setup_args(self, arg_parser):
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


    def _load_defaults(self):
        with open(self._cfg_path, 'r') as fd:
            self._haproxy_options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self._haproxy_options, indent = 4))
        # TODO validations for configs.


    def process_inputs(self, arg_parser):
        program_args = arg_parser.parse_args()

        if program_args.show_haproxy_file_format:
            print(self._haproxy_options)
            return False
        elif program_args.haproxy_file:
            # Load haproxy file and merge options.
            new_options = {}

            with open(program_args.haproxy_file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
                self._haproxy_options.update(new_options)
            return True

        elif program_args.interactive:
            input_msg = ("Enter no of background processes for HAProxy:"
            " (default is {0}):".format(self._haproxy_options["haproxy"]["nbproc"]))
            self._haproxy_options["haproxy"]["nbproc"] = \
                input(input_msg) or \
                    self._haproxy_options["haproxy"]["nbproc"]

            input_msg = ("Enable ssl for frontend s3 server (true/false):"
            " (default is {0}):"\
                .format(self._haproxy_options["haproxy"]["frontend"]["s3server"]["ssl_enabled"]))
            self._haproxy_options["haproxy"]["frontend"]["s3server"]["ssl_enabled"] = \
                input(input_msg) or \
                    self._haproxy_options["haproxy"]["frontend"]["s3server"]["ssl_enabled"]

            input_msg = ("Enable ssl for frontend s3 auth server (true/false):"
            " (default is {0}):"\
                .format(self._haproxy_options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"]))
            self._haproxy_options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"] = \
                input(input_msg) or \
                    self._haproxy_options["haproxy"]["frontend"]["s3authserver"]["ssl_enabled"]

            input_msg = ("Enable ssl for backend s3 server (true/false): "
            "(default is {0}):"\
                .format(self._haproxy_options["haproxy"]["backend"]["s3server"]["ssl_enabled"]))
            self._haproxy_options["haproxy"]["backend"]["s3server"]["ssl_enabled"] = \
                input(input_msg) or \
                    self._haproxy_options["haproxy"]["backend"]["s3server"]["ssl_enabled"]

            input_msg = ("Enable ssl for backend s3 auth server (true/false): "
            "(default is {0}):"\
                .format(self._haproxy_options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"]))
            self._haproxy_options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"] = \
                input(input_msg) or \
                    self._haproxy_options["haproxy"]["backend"]["s3authserver"]["ssl_enabled"]
            # print(json.dumps(self._haproxy_options, indent = 4))
            return True
        else:
            # print("ERROR: No usable inputs provided.")
            return False

    def save(self):
        with open(self._cfg_path, 'w') as fd:
            yaml.dump(self._haproxy_options, fd, default_flow_style=False)
