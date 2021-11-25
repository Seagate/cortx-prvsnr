# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

from cortx.utils.conf_store import Conf
from cortx.provisioner import const

class Manifest:

    @staticmethod
    def _get_val(index, key):
        """Get value for given key."""
        val = Conf.get(index, key, '')
        return val

    @staticmethod
    def _get_elem_from_list(sub_str, search_list):
        """Get elements from list which contain given sub_str."""
        matched_string = [x for x in search_list if sub_str in x]
        return matched_string[0]

    @staticmethod
    def _get_build_id(rpm_name):
        """Get build-id from rpm-name."""
        build_id = ''
        num_list = []
        for s in rpm_name.split('-'):
            if s[0].isdigit():
                num_list.append(s)
        # Now num_list contains version and githash number
        # e.g ['2.0.0', '438_b3c80e82.x86_64.rpm']
        # Remove .noarch.rpm,.x86_64.rpm, .el7.x86_64, _e17.x86_64 from version string.
        if '.el7' in num_list[1]:
            num_list[1]= num_list[1].split(str('.el7'))[0]
        elif '_el7' in num_list[1]:
           num_list[1]= num_list[1].split('_el7')[0]
        elif '.noarch' in num_list[1]:
            num_list[1]=num_list[1].split('.noarch')[0]
        elif '.x86_64' in num_list[1]:
            num_list[1]=num_list[1].split('.x86_64')[0]
        build_id = num_list[0] + '.' + num_list[1]
        return build_id

class CortxRelease(Manifest):

    _release_info_url = f'yaml://{const.RELEASE_INFO_PATH}'
    _release_index = 'release'

    def __init__(self):
        """Load RELEASE.INFO."""
        Conf.load(self._release_index, self._release_info_url, fail_reload=False)

    def get_value(self, key: str):
        """Get value from RELEASE.INFO for given key."""
        value = Manifest._get_val(self._release_index, key)
        return value

    def get_version(self, component):
        """Get version for given component."""
        rpms = self.get_value('COMPONENTS')
        comp_rpm = Manifest._get_elem_from_list(component, rpms)
        version = Manifest._get_build_id(comp_rpm)
        return version

    def validate(self, cm_release=''):
        """Validate configmap release info with RELEASE.INFO, Return correct value."""
        release_info = {}
        is_valid = True
        keys = ['name', 'version']
        for key in keys:
            value = self.get_value(key.upper())
            if not cm_release or cm_release[key] != value:
                release_info[key] = value
                is_valid = False
        return is_valid, release_info
