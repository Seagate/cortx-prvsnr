#!/usr/bin/python3
import argparse
import os
import sys
import yaml

from components.cluster_cfg import ClusterCfg
from components.eoscore_cfg import EOSCoreCfg
from components.haproxy_cfg import HAProxyCfg
from components.release_cfg import ReleaseCfg
from components.s3client_cfg import S3ClientCfg
from components.s3server_cfg import S3ServerCfg
from components.sspl_cfg import SSPLCfg


# Directory path to pillar data file
__config_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "pillar"
    )


def __config_modules(arg_parser):
    # TODO: Dynamically load modules from ./utils/components as generator
    # Define component modules and setup args
    cfg_module = [
        ReleaseCfg(
            arg_parser,
            cfg_path=os.path.join(
                __config_dir,
                "components",
                "release.sls"
                )
            ),
        ClusterCfg(
            arg_parser,
            cfg_path=os.path.join(
                __config_dir,
                "components",
                "cluster.sls"
            )
        ),
        EOSCoreCfg(
            arg_parser,
            cfg_path=os.path.join(
                __config_dir,
                "components",
                "mero.sls"
            )
        ),
        HAProxyCfg(
            arg_parser,
            cfg_path=os.path.join(
                __config_dir,
                "components",
                "haproxy.sls"
            )
        ),
        S3ClientCfg(
            arg_parser,
            cfg_path=os.path.join(
                __config_dir,
                "components",
                "s3client.sls"
            )
        ),
        # S3ServerCfg(
        #     arg_parser,
        #     cfg_path=os.path.join(
        #         __config_dir,
        #         "components",
        #         "s3client.sls"
        #     )
        # ),
        SSPLCfg(
            arg_parser,
            cfg_path=os.path.join(
                __config_dir,
                "components",
                "sspl.sls"
            )
        )
    ]
    return cfg_module


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

    for mod in __config_modules(arg_parser):
        # print("Processing module: {0}".format(mod))
        if mod.process_inputs(arg_parser):
            mod.save()


if __name__ == "__main__":
    try:
        execute()
    except KeyboardInterrupt as e:
        print("\n\nWARNING: User aborted command. Partial data save/corruption might occur. It is advised to re-run the command.")
        sys.exit(1)
