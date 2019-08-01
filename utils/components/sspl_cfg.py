#!/usr/bin/env python3
import json
import os.path
import yaml
import re
from argparse import ArgumentParser, Namespace

from .base_cfg import BaseCfg


class SSPLCfg(BaseCfg):
    __options = {}
    __cfg_path = ""
    __schema = {}


    def __init__(self, cfg_path: str=None, arg_parser: ArgumentParser=None):
        self.__schema_path = os.path.join(os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                ),
                "sspl_schema.yaml"
            )
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
                "sspl.sls"
            )

        if os.path.exists(self.__cfg_path):
            self.__load_defaults()

        if arg_parser:
            self.__setup_args(arg_parser)


    def __setup_args(self, arg_parser=None):

        if not arg_parser:
            raise Exception("__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            '--sspl-file',
            dest = 'sspl_file',
            action="store",
            help='Yaml file with sspl configs')
        arg_parser.add_argument(
            '--show-sspl-file-format',
            dest = 'show_sspl_file_format',
            action="store_true",
            help='Display Yaml file format for sspl configs')


    def __load_defaults(self):
        with open(self.__cfg_path, 'r') as fd:
            self.__options = yaml.load(fd, Loader=yaml.FullLoader)
        # print(json.dumps(self._release_options, indent = 4))
        # TODO validations for configs.
        with open(self.__schema_path, 'r') as fd:
            self.__schema = yaml.safe_load(fd)
        try:
            self.validate(self.__schema, self.__options)
        except Exception as e:
            print("Validation Failed for {} : {}".format("sspl.sls",str(e)))


    def process_inputs(self, program_args: Namespace) -> bool:

        if program_args.interactive:
            input("\nAccepting interactive inputs for pillar/sspl.sls. Press any key to continue...")

            input_msg = ("Enter sspl role on this system: ({0}): ".format(
                    self.__options["sspl"]["role"]
                )
            )
            self.__options["sspl"]["role"] = (
                input(input_msg)
                or
                self.__options["sspl"]["role"]
            )
            # print(json.dumps(self._release_options, indent = 4))
            return True

        elif program_args.show_sspl_file_format:
            print(yaml.dump(self.__options, default_flow_style=False, width=1, indent=4))
            return False

        elif program_args.sspl_file:
            if not os.path.exists(program_args.sspl_file):
                raise FileNotFoundError("Error: No file exists at location sepecified by argument '--sspl-file'.")

            # Load sspl file and merge options.
            new_options = {}
            with open(program_args.sspl_file, 'r') as fd:
                new_options = yaml.load(fd, Loader=yaml.FullLoader)
                self.__options.update(new_options)
            return True

        else:
            print("Error: No usable inputs provided.")
            return False


    def save(self):
        with open(self.__cfg_path, 'w') as fd:
            yaml.dump(self.__options, fd, default_flow_style=False, indent=4)


    def validate(self, schema_dict: dict, pillar_dict: dict) -> bool:
        """
        This function validates the pillar dict with the schema dict

        Parameters :
        -----------
        schema_dict : dict
        The schema dict representation of a pillar data
        pillar_dict : dict
        The data dict of a pillar data

        Returns:
        -------
        bool
        True if pillar dict is validated with schema dict
        """
        for key, value in schema_dict.items():
            if key in pillar_dict:
                if pillar_dict[key].__class__.__name__ == schema_dict[key]["type"]:
                    if pillar_dict[key] is None and "required" in schema_dict[key] and schema_dict[key]["required"]:
                        if "default" in schema_dict[key]:
                            pillar_dict[key] = schema_dict[key]["default"]
                        else:
                            raise Exception(
                                "Default value missing for a required key {}".format(key))
                    if isinstance(pillar_dict[key], dict):
                        self.validate(schema_dict[key]["schema"], pillar_dict[key])
                    elif "format" in schema_dict[key] and schema_dict[key]["format"] == "ip-address":
                        match_exp = re.match(
                            r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", pillar_dict[key])
                        if not (bool(match_exp) and all(
                                map(lambda n: 0 <= int(n) <= 255, match_exp.groups()))):
                            raise Exception(
                                "ip-address is of invalid format for key {}".format(key))
                    if "option" in schema_dict[key] and pillar_dict[key].lower() not in schema_dict[key]["option"].lower().split("/"):
                        raise Exception("Unsupported value for key {}. Value should be one of {} ".format(key,schema_dict[key]["option"].split("/")))
                else:
                    raise Exception("Invalid Input for key {}. Expected {} instead of {}".format(
                        key, schema_dict[key]["type"], pillar_dict[key].__class__.__name__))
            else:
                raise Exception("Key not found {}".format(key))
        return True
