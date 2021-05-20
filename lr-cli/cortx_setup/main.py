#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

from pathlib import Path
from .log import Log
import argparse
import yaml
from . import commands


def handle_parser(subparsers, name, cls_name):
    parser = subparsers.add_parser(name)
    cls = getattr(commands, cls_name)
    args = cls(logger=Log.logger).get_args()
    for arg, value in args.items():
        cmd = arg
        if value['optional']:
            cmd = "--"+arg
        value.pop('optional')
        parser.add_argument(cmd, **value)
    parser.set_defaults(command=cls_name)


def handle_sub_parser(subparsers, name):
    parser = subparsers.add_parser(name)
    return parser


def handle_apis(parser, apis):
    subparsers = parser.add_subparsers()
    for key, value in apis.items():
        if isinstance(value, dict):
            new_parser = handle_sub_parser(subparsers, key)
            handle_apis(new_parser, value)
        else:
            handle_parser(subparsers, key, value)


def main():
    Log._get_logger("nodecli", "INFO", "/var/log/seagate/provisioner/")
    parent = Path(__file__).resolve().parent
    pa = Path(parent / 'api_spec.yaml')
    apis = yaml.safe_load(pa.read_text())
    parser = argparse.ArgumentParser(prog='cortx_setup CLI ')
    handle_apis(parser, apis)

    args = parser.parse_args()
    args = vars(args)
    cls_name = args.pop('command')
    cls = getattr(commands, cls_name)
    cls(logger=Log.logger).run(**args)


if __name__ == '__main__':
    main()
