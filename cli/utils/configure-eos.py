#!/usr/bin/python3
import argparse
import os
import sys
import yaml

from components.base_cfg import BaseCfg
from components.cluster_cfg import ClusterCfg
from components.eoscore_cfg import EOSCoreCfg
from components.haproxy_cfg import HAProxyCfg
from components.release_cfg import ReleaseCfg
from components.s3client_cfg import S3ClientCfg
from components.s3server_cfg import S3ServerCfg
from components.sspl_cfg import SSPLCfg
from components.generic_cfg import GenericCfg

def __config_modules(arg_parser):
    # TODO: Dynamically load modules from ./utils/components as generator
    # Define component modules and setup args

    module_map = {
        'cluster': GenericCfg(
            component='cluster',
            arg_parser=arg_parser.add_parser(
                'cluster',
                help='modify provisioning data for cluster config.'
            )
        ),
        'eoscore': GenericCfg(
            component='eoscore',
            arg_parser=arg_parser.add_parser(
                'eoscore',
                help='modify provisioning data for eoscore config.'
            )
        ),
        'haproxy': GenericCfg(
            component='haproxy',
            arg_parser=arg_parser.add_parser(
                'haproxy',
                help='modify provisioning data for haproxy config.'
            )
        ),
        'release': GenericCfg(
            component='release',
            arg_parser=arg_parser.add_parser(
                'release',
                help='modify provisioning data for release config.'
            )
        ),
        's3client': GenericCfg(
            component='s3client',
            arg_parser=arg_parser.add_parser(
                's3client',
                help='modify provisioning data for s3client config.'
            )
        ),
        's3server': GenericCfg(
            component='s3server',
            arg_parser=arg_parser.add_parser(
                's3server',
                help='modify provisioning data for s3server config.'
            )
        ),
        'sspl': GenericCfg(
            component='sspl',
            arg_parser=arg_parser.add_parser(
                'sspl',
                help='modify provisioning data for sspl config.'
            )
        )
    }
    return module_map


def execute():
    arg_parser = argparse.ArgumentParser(
        description='Provisioner script for single node'
    )

    arg_parser.add_argument(
        '-i',
        '--interactive',
        action="store_true",
        help='interactive mode, overrides the command line arguments.'
    )

    sub_parser = arg_parser.add_subparsers(
        dest='subparser_name',
        help='Specifies component for which the static provisioning data is to be updated.'
    )
    sub_parser.add_parser(
        'all',
        help='Iterate over all modules.'
    ),

    eos_mods = __config_modules(sub_parser)
    parser = arg_parser.parse_args()
    # print("Parser_args: {0}".format(parser))

    for k, v in eos_mods.items():
        # print("Processing component object: {0}".format(k))
        if parser.subparser_name and 'all' in parser.subparser_name:
            if v.process_inputs(parser):
                v.save()
        elif parser.subparser_name and (k in parser.subparser_name):
            if v.process_inputs(k, parser):
                v.save()
            break


if __name__ == "__main__":
    try:
        execute()
    except KeyboardInterrupt as e:
        print("\n\nWARNING: User aborted command. Partial data save/corruption might occur. It is advised to re-run the command.")
        sys.exit(1)
