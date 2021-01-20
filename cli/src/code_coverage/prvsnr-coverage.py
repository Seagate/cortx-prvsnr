#!/usr/bin/python3

import argparse
import subprocess
import sys
import os.path
import pathlib

def _run_command(cmd):
    try:
        res = subprocess.run(cmd, shell=True)
        if res.returncode:
            print(f"failed to run command {cmd} ")
            sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)

def install_coverage():
    print("Installing prerequisites")
    _run_command(
        f"yum install -y gcc cpp python3-devel"
    )
    _run_command(
        f"pip3 install -U api/python"
    )
    _run_command(
        f"pip3 install -r test-requirements.txt"
    )

def prvsnr_coverage():
    print("Executing provisioner test cases and generating coverage report")
    _run_command(
        f"coverage run -m pytest \
        --cov test/ --cov-report=xml"
    )
    if os.path.isfile(f'coverage.xml'):
        print("Coverage report generated successfully!!")
    else:
        print("Coverage report generation failed!!")
        sys.exit(1)
    print("Done")

def parse_args():
    parser = argparse.ArgumentParser(description='''Provisioner code-coverage automation ''')
    args=parser.parse_args()
    return args

if __name__ == "__main__":
    try:
        args = parse_args()
        install_coverage()
        prvsnr_coverage()
    except KeyboardInterrupt:
        print("\n\nWARNING: User aborted command, It is advised to re-run the command.")
        sys.exit(1)
