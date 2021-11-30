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
from cortx.provisioner.log import Log


class Manifest:

    @staticmethod
    def _get_val(index, key):
        """Get value for given key."""
        val = Conf.get(index, key, '')
        return val

    @staticmethod
    def _get_elem_from_list(sub_str: str, search_list: list):
        """Get elements from list which contain given sub_str."""
        matched_string = ''
        try:
            matched_string = [x for x in search_list if sub_str in x][0]
        except IndexError:
            Log.error(f'Key not found for key {sub_str} in {search_list}.')
        return matched_string

    @staticmethod
    def _get_build_version(rpm_name: str):
        """Get version from rpm-name."""
        version = ''
        temp_list = []
        try:
            for element in rpm_name.split('-'):
                if element[0].isdigit():
                    temp_list.append(element)
            # Now num_list contains version and githash number
            # e.g ['2.0.0', '438_b3c80e82.x86_64.rpm']
            # Remove .noarch.rpm,.x86_64.rpm, .el7.x86_64, _e17.x86_64 from version string.
            if '.el7' in temp_list[1]:
                temp_list[1] = temp_list[1].split(str('.el7'))[0]
            elif '_el7' in temp_list[1]:
                temp_list[1] = temp_list[1].split('_el7')[0]
            elif '.noarch' in temp_list[1]:
                temp_list[1] = temp_list[1].split('.noarch')[0]
            elif '.x86_64' in temp_list[1]:
                temp_list[1] = temp_list[1].split('.x86_64')[0]
            version = temp_list[0] + '-' + temp_list[1]
        except IndexError as e:
            Log.error(f'Exception occurred {e}.')
        return version

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

    def get_version(self, component: str):
        """Get version for given component."""
        rpms = self.get_value('COMPONENTS')
        component_rpm = Manifest._get_elem_from_list(component, rpms)
        version = Manifest._get_build_version(component_rpm)
        return version

    def validate(self, cm_release: dict = {}):
        """Validate configmap release info with RELEASE.INFO, Return correct value."""
        release_info = {}
        is_valid = True
        keys = ['name', 'version']
        for key in keys:
            value = self.get_value(key.upper())
            if not cm_release or cm_release.get(key) != value:
                release_info[key] = value
                is_valid = False
        return is_valid, release_info
