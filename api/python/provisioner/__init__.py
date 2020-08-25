#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
    sw_update,
    fw_update,
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
    execute_remote_command
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
    'sw_update',
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
    'execute_remote_command',
    'UNCHANGED',
    'DEFAULT',
    'UNDEFINED',
    'MISSED',
    'NONE',
    'ALL_HOSTS',
    'ALL_MINIONS'
]
