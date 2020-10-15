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

import logging
from .scripts.utils.common import setup_logging
from .config import UNBOXING_PRE_CHECK, UNBOXING_POST_CHECK

logger = logging.getLogger(__name__)

class unboxing():

    @staticmethod
    def start_validation(chk_list):
        """Starts check list validation"""
        for check in chk_list:
            res = getattr(chk_list[check][0](), chk_list[check][1])()
            print(f"Output: {res}")


    def run_pre_check(self):
        """Pre-check function for unboxing"""
        self.start_validation(UNBOXING_PRE_CHECK)

    def run_post_check(self):
        """Post-check function for unboxing"""
        self.start_validation(UNBOXING_POST_CHECK)



if __name__ == '__main__':
    import argparse

    setup_logging()

    parser = argparse.ArgumentParser()

    parser.add_argument("--precheck", action='store_true',
                        help="Unboxing Pre check validation")
    parser.add_argument("--postcheck", action='store_true',
                        help="Unboxing Post check validation")

    args = parser.parse_args()

    ub = unboxing()

    if args.precheck:
        ub.run_pre_check()
    elif args.postcheck:
        ub.run_post_check()
    else:
        parser.print_help()

