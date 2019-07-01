import json
import yaml

class SSPLCfg:
    _sspl_options = {}
    _cfg_path = ""

    def __init__(self, arg_parser, cfg_path):
        self._cfg_path = cfg_path
        self._setup_args(arg_parser)
        self._load_defaults()

    def _setup_args(self, arg_parser):
        # TODO - validate for accidental override
        arg_parser.add_argument('--sspl-file', action="store", \
            help='Yaml file with sspl configs')
        arg_parser.add_argument('--show_sspl_file_format', \
            action="store_true",\
            help='Display Yaml file format for sspl configs')

    def _load_defaults(self):
        with open(self._cfg_path, 'r') as fd:
            self._sspl_options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self._release_options, indent = 4))
        # TODO validations for configs.

    def process_inputs(self, program_args):
        if program_args.show_sspl_file_format:
            print(self._sspl_options)
            return False
        elif program_args.sspl_file:
            # Load sspl file and merge options.
            new_options = {}
            with open(program_args.sspl_file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
                self._sspl_options.update(new_options)
            return True
        elif program_args.interactive:
            input_msg = ("Enter sspl role on this system: (default is {0}):"\
                .format(self._sspl_options["sspl"]["role"]))
            self._sspl_options["sspl"]["role"] = input(input_msg) or \
                self._sspl_options["sspl"]["role"]
            # print(json.dumps(self._release_options, indent = 4))
            return True

    def save(self):
        with open(self._cfg_path, 'w') as fd:
            yaml.dump(self._sspl_options, fd, default_flow_style=False)
