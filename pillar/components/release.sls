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

release:
    product: LR2
    setup: cortx
    type: internal  # value 'bundle' will switch to bundled distribution
                    # repo structure assumptions, where 'target_build'
                    # defines the base url:
                    # <base_url>/
                    #   rhel7.7 or centos7.7   <- OS ISO is mounted here
                    #   3rd_party              <- CORTX 3rd party ISO is mounted here
                    #   cortx_iso              <- CORTX ISO (main) is mounted here
    target_build: http://cortx-storage.colo.seagate.com/releases/cortx/github/release/rhel-7.7.1908/last_successful/
    update:
        base_dir: /opt/seagate/cortx/updates
        repos: {}  # dictionary with (release, source) pairs,
                   # source should be either an url (starts with 'http://' or 'https://')
                   # or one of special values: 'dir', 'iso'
    upgrade:
        base_dir: /opt/seagate/cortx/upgrades
        repos: {}  # dictionary with (release, source) pairs,
                   # source should be either an url (starts with 'http://' or 'https://')
                   # or one of special values: 'dir', 'iso'
