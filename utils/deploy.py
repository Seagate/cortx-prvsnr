import sys
import os
import argparse
import yaml

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    release_pillar = "../pillar/components/release.sls"
    release_pillar_sls = os.path.join(script_dir, release_pillar)

    parser = argparse.ArgumentParser(description='Provisioner script for single node')
    parser.add_argument('-i', '--interactive', action="store_true", help='interactive mode')
    parser.add_argument('--release', help='EES release version as required in CI repo, e.g. EES_Sprint1')
    args = parser.parse_args()

    if args.interactive:
        release = raw_input("Enter target eos release version:")
    else:
        release = args.release

    with open(release_pillar_sls, 'r+') as release_sls:
        release_dict = yaml.load(release_sls)
        build = release_dict["eos_release"]["target_build"]
        release_dict["eos_release"]["target_build"] = release
        release_sls.seek(0)
        yaml.dump(release_dict, release_sls, default_flow_style=False)
