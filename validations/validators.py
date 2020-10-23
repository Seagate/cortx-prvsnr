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
import logging
from scripts.factory.pre_flight_check import PreFlightValidationsCall
from scripts.factory.cluster_readiness_check import ClusterValidationsCall
from scripts.factory.cortx_check import CortxValidationsCall
from scripts.factory.unboxing_readiness_check import UnboxingValidationsCall

logger = logging.getLogger(__name__)


class Validators():
    """Validation of all checks for given request."""

    @staticmethod  # noqa: C901
    def factory_checks(args):
        if args.postcheck:
            check_list = config.FACTORY_POST_CHECK
        elif args.precheck:
            check_list = config.FACTORY_PRE_CHECK
        elif args.replacenode:
            check_list = config.REPLACE_NODE_CHECK
        elif args.fwupdate:
            check_list = config.FW_UPDATE_CHECK
        elif args.unboxing:
            check_list = config.UNBOXING_CHECK
        elif args.c:
            check_list = {args.c: config.ALL_CHECKS[args.c]}
        else:
            print("No valid argument is passed")

        if len(check_list.keys()) < 1:
            print("Check is not available for this flag")

        for check, cls in check_list.items():
            logger.info(f"Check name {check}")
            obj = globals()[cls]()
            res = getattr(obj, check)()
            if res:
                if res['ret_code']:
                    print(f"{check}: {res['message']}......[Failed]")
                    print(f"Response: {res}\n")
                else:
                    print(f"{check}: {res['message']}......[Success]\n")


if __name__ == '__main__':
    import argparse
    import sys
    #from scripts.utils.log import setup_logging

    #setup_logging()

    argParser = argparse.ArgumentParser()
    argParser.add_argument(
              "--precheck", action='store_true',
              help="Factory deployment Pre check validation")
    argParser.add_argument(
              "--postcheck", action='store_true',
              help="Factory deployment Post check validation")
    argParser.add_argument(
              "--replacenode", action='store_true',
              help="Software update check validation")
    argParser.add_argument(
              "--fwupdate", action='store_true',
              help="Firmware update check validation")
    argParser.add_argument(
              "--unboxing", action='store_true',
              help="Unboxing check validation")
    argParser.add_argument(
              "-c", type=str, choices=config.ALL_CHECKS.keys(),
              help="Name of validation to check")
    argParser.set_defaults(func=Validators.factory_checks)
    args = argParser.parse_args()
    args.func(args)
    sys.exit(0)
