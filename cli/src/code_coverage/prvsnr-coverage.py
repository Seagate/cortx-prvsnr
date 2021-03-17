#!/usr/bin/python3

import argparse
import os.path
import subprocess
import sys

safe_commands = [
    'yum',
    'install',
    'coverage'
]


def _run(cmd):
    if not set(safe_commands).intersection(cmd.split()):
        raise Exception(
            f"Execution of command {cmd} is identified "
            "as a command with risky behavior. "
            f"Hence, execution of command {cmd} is prohibited."
        )
    try:
        subprocess.run(cmd.split(), shell=False, check=True)
    except Exception as e:
        print(e)
        sys.exit(1)


def install_coverage():
    print("Installing prerequisites")
    _run(
        "yum install -y gcc cpp python3-devel"
    )
    _run(
        "pip3 install -U api/python[test]"
    )


def prvsnr_coverage():
    print("Executing provisioner test cases and generating coverage report")
    _run(
        "coverage run -m pytest -m unit\
        --cov test/ --cov-report=xml"
    )
    if os.path.isfile('coverage.xml'):
        print("Coverage report generated successfully!!")
    else:
        print("Coverage report generation failed!!")
        sys.exit(1)
    print("Done")


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Provisioner code-coverage automation."
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    try:
        _parse_args()
        install_coverage()
        prvsnr_coverage()
    except KeyboardInterrupt:
        print(
            "\n\nWARNING: User aborted command, "
            "It is advised to re-run the command."
        )
        sys.exit(1)
