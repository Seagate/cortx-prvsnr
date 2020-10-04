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

# TODO IMPROVE EOS-8473 move to pillar to make configurable
{% set install_dir = '/opt/seagate/cortx/provisioner' %}

repo_installed:
  file.recurse:
    - name: {{ install_dir }}
    - source: salt://provisioner/files/repo
    - keep_source: True
    - clean: False  # True would clean up generated_configs dir
                    # We don't want the directory to be cleaned-up
