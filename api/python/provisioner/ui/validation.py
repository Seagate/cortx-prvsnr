#!/usr/bin/env python
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
#
import re
import ipaddress


class Validation:

    @staticmethod
    def ipv4(ip):
        try:
            value = None
            result = True
            if ip:
                value = ipaddress.IPv4Address(ip)
                # TODO : Improve logic internally convert ip to
                # canonical forms.
                if ip != str(value):
                    result = False
        except ValueError:
            result = False
        return result

    @staticmethod
    def hostname(hostname):
        result = True
        # TODO: Improve logic for validation of hostname
        hostname_regex = r"^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,6}$"
        if len(hostname) > 253:
            result = False
        else:
            if not re.search(hostname_regex, hostname):
                result = False
        return result
