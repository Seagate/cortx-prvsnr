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

from .__metadata__ import (  # noqa: F401
    __title__,
    __version__,
    __author__,
    __author_email__,
    __maintainer__,
    __maintainer_email__,
    __url__,
    __description__,
    __long_description__,
    __download_url__,
    __license__,
)

from .api import (  # noqa: F401
    set_api,
    auth_init,
    get_result,
    pillar_get,
    pillar_set,
    get_params,
    set_params,
    set_ntp,
    set_network,
    set_swupdate_repo,
    set_swupgrade_repo,
    sw_update,
    sw_upgrade,
    fw_update,
    sw_rollback,
    set_ssl_certs,
    get_cluster_id,
    get_node_id,
    reboot_server,
    reboot_controller,
    shutdown_controller,
    configure_cortx,
    create_user,
    replace_node,
    get_release_version,
    get_factory_version,
    cmd_run,
    get_setup_info,
    grains_get,
    set_hostname,
    setup_firewall
)

from .values import (  # noqa: F401
    UNCHANGED, DEFAULT, UNDEFINED, MISSED, NONE
)

from .config import (  # noqa: F401
    ALL_MINIONS as ALL_HOSTS, ALL_MINIONS
)

__all__ = [
    'set_api',
    'auth_init',
    'get_result',
    'pillar_get',
    'pillar_set',
    'get_params',
    'set_params',
    'set_ntp',
    'set_network',
    'set_swupdate_repo',
    'set_swupgrade_repo',
    'sw_update',
    'sw_upgrade',
    'sw_rollback',
    'set_ssl_certs',
    'fw_update',
    'get_cluster_id',
    'get_node_id',
    'reboot_server',
    'reboot_controller',
    'shutdown_controller',
    'configure_cortx',
    'create_user',
    'replace_node',
    'get_release_version',
    'get_factory_version',
    'cmd_run',
    'get_setup_info',
    'grains_get',
    'set_hostname',
    'UNCHANGED',
    'DEFAULT',
    'UNDEFINED',
    'MISSED',
    'NONE',
    'ALL_HOSTS',
    'ALL_MINIONS'
]
