import json
import sys
import yaml

class ReleaseCfg:
    _release_options = {}
    _cfg_path = ""

    def __init__(self, arg_parser, cfg_path):
        self._cfg_path = cfg_path
        self._setup_args(arg_parser)
        self._load_defaults()

    def _setup_args(self, arg_parser):
        # TODO - validate for accidental override
        arg_parser.add_argument('--release', \
            help='Release version as required in CI repo, e.g. EES_Sprint1')
        arg_parser.add_argument('--release-file', action="store", \
            help='Yaml file with release configs')
        arg_parser.add_argument('--show-release-file-format', \
            action="store_true",\
            help='Display Yaml file format for release configs')

    def _load_defaults(self):
        with open(self._cfg_path, 'r') as fd:
            self._release_options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self._release_options, indent = 4))
        # TODO validations for configs.

    def process_inputs(self, program_args):
        if program_args.show_release_file_format:
            print(self._release_options)
            return False
        elif program_args.release_file:
            # Load release file and merge options.
            new_options = {}
            with open(program_args.release_file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
                self._release_options.update(new_options)
            return True
        elif program_args.interactive:
            input_msg = ("Enter target eos release version: (default is {0}):"\
                .format(self._release_options["eos_release"]["target_build"]))
            self._release_options["eos_release"]["target_build"] = \
                    input(input_msg) or self._release_options["eos_release"]["target_build"]
            return True
        else:
            self._release_options["eos_release"]["target_build"] = program_args.release
            # print(json.dumps(self._release_options, indent = 4))
            return True

    def save(self):
        with open(self._cfg_path, 'w') as fd:
            yaml.dump(self._release_options, fd, default_flow_style=False)
