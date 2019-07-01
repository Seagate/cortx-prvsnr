import argparse
import os
import sys
import yaml

from components.cluster_cfg import ClusterCfg
from components.eoscore_cfg import EOSCoreCfg
from components.haproxy_cfg import HAProxyCfg
from components.release_cfg import ReleaseCfg
from components.s3client_cfg import S3ClientCfg
from components.sspl_cfg import SSPLCfg

if __name__ == "__main__":

    try:

        arg_parser = argparse.ArgumentParser(
            description='Provisioner script for single node')
        arg_parser.add_argument('-i', '--interactive', action="store_true", \
            help='interactive mode, overrides the command line arguments.')

        script_dir = os.path.dirname(os.path.realpath(__file__))
        _config_dir = os.path.join(script_dir, "..", "pillar")

        # Define component modules and setup args
        _modules = [
            ReleaseCfg(arg_parser, cfg_path=os.path.join(
                _config_dir, "components", "release.sls")),
            ClusterCfg(arg_parser, cfg_path=os.path.join(
                _config_dir, "components", "cluster.sls")),
            SSPLCfg(arg_parser, cfg_path=os.path.join(
                _config_dir, "components", "sspl.sls")),
            EOSCoreCfg(arg_parser, cfg_path=os.path.join(
                _config_dir, "components", "mero.sls")),
            HAProxyCfg(arg_parser, cfg_path=os.path.join(
                _config_dir, "components", "haproxy.sls")),
            S3ClientCfg(arg_parser, cfg_path=os.path.join(
                _config_dir, "components", "s3client.sls"))
        ]

        # Process the program args
        _program_args = arg_parser.parse_args()

        for mod in _modules:
            if mod.process_inputs(_program_args):
                mod.save()
    except KeyboardInterrupt as e:
        print("\n\nWARNING: User aborted command. Partial data save/corruption might occur. It is advised to re-run the command.")
        sys.exit(1)
