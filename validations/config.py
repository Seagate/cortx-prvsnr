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

UNBOXING_PRE_CHECK = {
    # 'bmc_validation' : [BmcCheck, 'is_bmc_accessible'],
    'verify_public_data_ip' : 'NetworkValidations',
}

UNBOXING_POST_CHECK = {
}

ALL_CHECKS = {
}

for check in (
            UNBOXING_PRE_CHECK,
            UNBOXING_POST_CHECK ):
    ALL_CHECKS.update(check)
