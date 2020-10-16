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

import config
from scripts.factory.server_check import ServerValidations
from scripts.factory.network_check import NetworkChecks
from scripts.factory.storage_check import StorageValidations
from scripts.factory.controller_check import ControllerValidations

class_mapper = {
    'server_validation': ServerValidations,
    'netowrk_validation': NetworkChecks,
    'storage_validation': StorageValidations,
    'controller_validation': ControllerValidations
}


class Validators():
    ''' Validator class :validation of all checks for given request '''

    @staticmethod
    def factory_checks(args):
        if args.postcheck:
            check_list = config.FACTORY_POST_CHECK
        if args.precheck:
            check_list = config.FACTORY_PRE_CHECK
        for check, cls in check_list.items():
            res = getattr(class_mapper[cls], check)()
            if res:
                if res['ret_code']:
                    print(f"{check}: Failed : {res['message']}")
                    print(f"Response: {res}\n")
                else:
                    print(f"{check}: Success : {res['message']}\n")


if __name__ == '__main__':
    import argparse
    import sys
    argParser = argparse.ArgumentParser()
    argParser.add_argument(
              "--precheck", action='store_true',
              help="Factory deployment Pre check validation")
    argParser.add_argument(
              "--postcheck", action='store_true',
              help="Factory deployment Post check validation")
    argParser.set_defaults(func=Validators.factory_checks)
    args = argParser.parse_args()
    args.func(args)
    sys.exit(0)
