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

import logging

from typing import Optional

from .vendor import attr
from .config import LOCAL_MINION
from .salt import cmd_run
from .utils import ensure, run_subprocess_cmd, load_json_str
from . import errors
from .hare import check_cluster_is_online

try:
    from ha.core.cluster.cluster_manager import CortxClusterManager
except ImportError:
    CortxClusterManager = None

try:
    run_subprocess_cmd("cortx --help")
except errors.SubprocessCmdError:
    cortx_cmd = None
else:
    cortx_cmd = "cortx"


logger = logging.getLogger(__name__)


@attr.s(auto_attribs=True)
class ClusterManager:
    ha_ccm: Optional[CortxClusterManager] = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        if CortxClusterManager:
            self.ha_ccm = CortxClusterManager()

    @property
    def is_pcs(self):
        return not (self.ha_ccm or cortx_cmd)

    def cluster_status(self):
        # FIXME need to process different output formats here
        #       and return a common result
        if self.ha_ccm:
            return self.ha_ccm.cluster_controller.status()

        if cortx_cmd:
            ret = cmd_run(f"{cortx_cmd} cluster status", targets=LOCAL_MINION)
        else:
            ret = cmd_run('pcs status', targets=LOCAL_MINION)

        ret = next(iter(ret.values()))
        if cortx_cmd:
            ret = load_json_str(ret)
        return ret

    def cluster_stop(self):
        # FIXME need to process different output formats here
        #       and return a common result
        if self.ha_ccm:
            return self.ha_ccm.cluster_controller.stop()

        if cortx_cmd:
            ret = cmd_run(f"{cortx_cmd} cluster stop", targets=LOCAL_MINION)
        else:
            ret = cmd_run('pcs cluster stop --all', targets=LOCAL_MINION)

        ret = next(iter(ret.values()))
        if cortx_cmd:
            ret = load_json_str(ret)
        return ret

    def cluster_start(self):
        # FIXME need to process different output formats here
        #       and return a common result
        if self.ha_ccm:
            return self.ha_ccm.cluster_controller.start()

        if cortx_cmd:
            ret = cmd_run(f"{cortx_cmd} cluster start", targets=LOCAL_MINION)
        else:
            ret = cmd_run('pcs cluster start --all', targets=LOCAL_MINION)

        ret = next(iter(ret.values()))
        if cortx_cmd:
            ret = load_json_str(ret)
        return ret

    def is_offline(self):
        ret = self.cluster_status()
        if self.is_pcs:
            return ('OFFLINE:' in ret)
        else:
            return ret['status'] == 'Succeeded' and ret['output'] == 'offline'

    def is_online(self):
        if self.is_pcs:
            return check_cluster_is_online()
        else:
            ret = self.cluster_status()
            return ret['status'] == 'Succeeded' and ret['output'] == 'online'


cluster_manager = ClusterManager()


def ensure_cluster_is_stopped(tries: int = 30, wait: float = 10):
    cluster_manager.cluster_stop()
    # NOTE: In new HA API cluster stop command is async.
    # So ensure block is added
    ensure(cluster_manager.is_offline, tries=tries, wait=wait)


def ensure_cluster_is_started(tries: int = 30, wait: float = 10):
    cluster_manager.cluster_start()
    ensure(cluster_manager.is_online, tries=tries, wait=wait)


def check_cluster_health_status():
    """
    Wrapper over API of the Cortx Ha which provides the capability to check
    the health status of cluster.

    Raises
    ------
    ProvisionerError
        raise this exception if the number of tries was exceeded
    """
    logger.debug("Checking the CORTX cluster health")
    wait = 10
    if cluster_manager.is_pcs:
        # TODO IMPROVE EOS-8940 here we rely on utility_scripts.sh as it
        #      has its own looping logic, so only one try here
        tries = 1
    else:
        tries = 20

    ensure(cluster_manager.is_online, tries=tries, wait=wait)


def cluster_stop(tries: int = 30, wait: float = 10):
    """
    Wrapper over HA CLI command to stop the cluster

    Parameters
    ----------
    tries: int
        number of tries

    wait: float
        wait time in seconds between tries

    Raises
    ------
    ProvisionerError
        raise this exception if the number of tries was exceeded

    """
    logger.debug("Stopping the CORTX cluster")
    ensure_cluster_is_stopped(tries=tries, wait=wait)


def cluster_start(tries: int = 30, wait: float = 10):
    """
    Wrapper over HA CLI command to start the cluster

    Parameters
    ----------
    tries: int
        number of tries

    wait: float
        wait time in seconds between tries

    Raises
    ------
    ProvisionerError
        raise this exception if the number of tries was exceeded

    """
    logger.debug("Stopping the CORTX cluster health")
    ensure_cluster_is_started(tries=tries, wait=wait)
