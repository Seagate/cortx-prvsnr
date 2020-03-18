#!/usr/bin/env python3
import json
import os.path
import yaml
from shutil import copy

from argparse import ArgumentParser, Namespace
from  srv._modules.commons import _update_dict
from .base_cfg import BaseCfg


class GenericCfg(BaseCfg):

    def __init__(self,component: str=None, cfg_path: str=None, arg_parser: ArgumentParser=None): 
        if cfg_path:
            self._cfg_path = cfg_path
        elif component == "global":
            self._cfg_path = os.path.join(
                self._pillar_path,
                "components/samples/template.yml"
            )
        else:
           self._cfg_path = os.path.join(
                self._pillar_path,
                "components",
                f"{component}.sls"
            )


        if arg_parser:
            self.__setup_args(component, arg_parser)


    def __setup_args(self,component, arg_parser=None):

        if not arg_parser:
            raise Exception("__setup_args() cannot be called without an argparse object")

        arg_parser.add_argument(
            f'--file',
            dest = f'file',
            action="store",
            help=f'Yaml file with {component} configs')
        arg_parser.add_argument(
            f'--show-file-format',
            dest = f'show_file_format',
            action="store_true",
            help=f'Display Yaml file format for {component} configs')
        arg_parser.add_argument(
            '--load-default',
            dest = 'load_default',
            action = 'store_true',
            help = 'Reset default values to a modified YAML file'
        )

    def __read_user_inputs(self, opt_tree: dict={}, parent: str='') -> dict:
        for k, v in opt_tree.items():
            if isinstance(v, dict):
                opt_tree[k] = self.__read_user_inputs(v, f'{parent}[{k}]')
            else:
                user_input = input(f"Enter value for {parent}[{k}] -> ({v}): ")
                opt_tree[k] = user_input if user_input else v

        return opt_tree


    def load_existing_config(self, component):
        if component == "global":
            eos_config = {}
            for key, value in self._options.items():
                sls_file = os.path.join(
                self._pillar_path,
                "components",
                f"{key}.sls"
                )
                if os.path.exists(sls_file):
                    new_options = {}
                    with open(sls_file, 'r') as fd:
                        new_options = yaml.safe_load(fd)
                        eos_config.update(new_options)
            self._options.update(eos_config)
                        
     
    def process_inputs(self, component, program_args: Namespace) -> bool:

        if program_args.interactive:
            input(f"\nAccepting interactive inputs for pillar/{component}.sls. Press any key to continue...")
            self.load_existing_config(component) 
            self._options = self.__read_user_inputs(self._options)

            # print(json.dumps(self._release_options, indent = 4))
            return True

        elif program_args.show_file_format:
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

        elif program_args.file:
            if not os.path.exists(program_args.file):
                raise FileNotFoundError(f"Error: No file exists at location sepecified by argument '--{component}-file'.")
            self.load_existing_config(component)
            # Load file and merge options.
            new_options = {}
            with open(program_args.file, 'r') as fd:
                new_options = yaml.safe_load(fd)
                _update_dict(self._options, new_options)
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
            if os.path.exists(args[1]):
                copy(args[1],args[1]+".bak")
            return func(*args)
        return backup

    @pillar_backup
    def store_in_file(self, path, data):
        with open(path, 'w') as fd:
            yaml.safe_dump(
                data,
                stream=fd,
                default_flow_style=False,
                canonical=False,
                width=1,
                indent=4
            )

    #@pillar_backup
    def save(self, component):
        data = {}
        sls_file = self._cfg_path 
        if component == "global":
            for key, value in self._options.items():
                data = {} 
                data[key] = value
                sls_file = os.path.join(
                self._pillar_path,
                "components",
                f"{key}.sls"
            )

                self.store_in_file(sls_file, data)
        else:
            self.store_in_file(sls_file, self._options)     

    def validate(self, schema_dict: dict, pillar_dict: dict) -> bool:
        pass
