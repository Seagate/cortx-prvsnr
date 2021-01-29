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

{% if "primary" in pillar["cluster"][grains["id"]]["roles"] -%}

{% set logfile = "/var/log/seagate/provisioner/sanity_tests.log" %}

Run CSM sanity tests:
  cmd.run:
    - name: /usr/bin/csm_test -f /opt/seagate/cortx/csm/test/test_data/args.yaml -t /opt/seagate/cortx/csm/test/plans/self_test.pln 2>&1 | tee -a {{ logfile }}

{% endif %}
