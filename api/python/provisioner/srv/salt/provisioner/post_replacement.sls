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
# please email opensource@seagate.com or cortx-questions@seagate.com."
#

Set replacement flag:
  file.managed:
    - name: /etc/profile.d/set_replacement_env.sh
    - contents: |
        #!/bin/bash
        test ${REPLACEMENT_NODE} || export REPLACEMENT_NODE=true
    - create: true

Apply changes:
  cmd.run:
    - name: 'source /etc/profile.d/set_replacement_env.sh'
    - require:
      - Set replacement flag