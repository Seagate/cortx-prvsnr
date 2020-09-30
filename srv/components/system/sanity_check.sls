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

# Fail provisioning if this check returns non-zero
#Check system hostname:
#  cmd.run:
#    - name: test $(salt --no-color srvnode-1 grains.get host|tail -1|tr -d "[:blank:]") == $(hostname)

Dummy placeholder for system.sanity_check:
  test.show_notification:
    - text: "A yaml file with comments results in minion non-zero exit"
