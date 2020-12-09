#!/bin/bash
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

set -eu

domain="${1:-$(hostname)}"

echo "Checking DNS resolution for domain '$domain'"

res="$(getent -s hosts:dns ahosts "$domain" | paste -sd " " -)"

if [[ -z "$res" ]]; then
    >&2 echo "No DNS data found"
    exit 1
fi

echo "Resolved into: '$res'"

exit 0

#ns_servers=$(dig +short NS "$domain" | paste -sd " " -)

#if [[ -z "$ns_servers" ]]; then
#    >&2 echo "No DNS servers found"
#    exit 1
#else
#    echo "DNS servers detected: $ns_servers"
#fi

#for ns in $ns_servers; do
#    echo "Trying NS '$ns'"
#    res=$(dig +short +timeout=3 "@${ns}" "$domain")

#    if [[ -z "$res" ]]; then
#        >&2 echo "DNS failed for NS '$ns'"
#        exit 1
#    fi
#done

#echo "Domain '$domain' is resolved by all DNS servers"
