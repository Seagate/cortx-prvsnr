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

from typing import Optional, Union, Tuple, List
from abc import ABC, abstractmethod

from .vendor import attr
from .config import (
    LOCAL_MINION,
    HACmdResult,
    HAClusterStatus
)
from .salt import cmd_run
from .utils import ensure, run_subprocess_cmd, load_json_str
from . import errors
from .values import MISSED
# from .hare import check_cluster_is_online

try:
    from ha.core.cluster.cluster_manager import CortxClusterManager
except ImportError:
    CortxClusterManager = None

CORTX_HA_TOOL = "cortx"


logger = logging.getLogger(__name__)


class ClusterManagerBase(ABC):

    def _run_cmd(self, cmd: str, json=False):
        ret = cmd_run(cmd, targets=LOCAL_MINION)
        ret = next(iter(ret.values()))
        return load_json_str(ret) if json else ret

    @abstractmethod
    def cluster_status(self):
        """Return the status."""

    @abstractmethod
    def cluster_stop(self):
        """Stop the cluster."""

    @abstractmethod
    def cluster_standby(self):
        """Standby the cluster."""

    @abstractmethod
    def cluster_start(self):
        """Start the cluster."""

    @abstractmethod
    def cluster_unstandby(self):
        """Unstandby the cluster."""

    @abstractmethod
    def is_offline(self):
        """Check whether cluster is offline."""

    @abstractmethod
    def is_online(self):
        """Check whether cluster is online."""


class ClusterManagerPCS(ClusterManagerBase):

    def cluster_status(self):
        return self._run_cmd('pcs status')

    def cluster_stop(self, standby=False):
        return self._run_cmd(
            "pcs cluster stop --all"
        )

    def cluster_standby(self):
        return self._run_cmd(
            "pcs cluster standby --all"
        )

    def cluster_start(self):
        return self._run_cmd('pcs cluster start --all')

    def cluster_unstandby(self):
        return self._run_cmd('pcs cluster unstandby --all')

    def _check_offline(self, status):
        return ('OFFLINE:' in status)

    def is_offline(self):
        # TODO naive implementation
        try:
            ret = self.cluster_status()
        except errors.SaltCmdResultError as exc:
            if (
                'cluster is not currently running on this node'
                not in str(exc.reason)
            ):
                logger.warning(f"Cluster status failed: {exc}")
            return True
        else:
            return self._check_offline(ret)

    def is_online(self):
        # TODO naive implementation
        try:
            ret = self.cluster_status()
        except errors.SaltCmdResultError as exc:
            logger.warning(f"Cluster status failed: {exc}")
            return False
        else:
            return not self._check_offline(ret)

    def is_standby(self):
        raise NotImplementedError


@attr.s(auto_attribs=True)
class HAResponse:
    status: str
    output: str
    error: str


class ClusterManagerCortxCmd(ClusterManagerBase):

    def _run_cmd(self, cmd: str):
        ret = super()._run_cmd(cmd, json=True)
        ret = HAResponse(**ret)
        if ret.status == HACmdResult.FAILED.value:
            raise errors.ProvisionerError(
                "HA command `{cmd}` failed with error: '{ret.error}'"
            )
        return ret

    def cluster_status(self):
        return self._run_cmd(f"{CORTX_HA_TOOL} cluster status")

    def cluster_stop(self, standby=False):
        return self._run_cmd(
            f"{CORTX_HA_TOOL} cluster stop"
        )

    def cluster_standby(self):
        raise NotImplementedError("Not supported by '{CORTX_HA_TOOL}' tool")

    def cluster_start(self):
        return self._run_cmd(f"{CORTX_HA_TOOL} cluster start")

    def cluster_unstandby(self):
        raise NotImplementedError("Not supported by '{CORTX_HA_TOOL}' tool")

    def check_status(
        self, status: Union[
            HAClusterStatus,
            Tuple[HAClusterStatus],
            List[HAClusterStatus]
        ]
    ):
        if isinstance(status, HAClusterStatus):
            status = [status]
        ret = self.cluster_status()
        _status = HAClusterStatus(ret.output)
        return _status in status

    def is_offline(self):
        return self.check_status(HAClusterStatus.OFFLINE)

    def is_online(self):
        return self.check_status(HAClusterStatus.OFFLINE)

    def is_standby(self):
        return self.check_status(HAClusterStatus.STANDBY)


@attr.s(auto_attribs=True)
class ClusterManagerCortxAPI(ClusterManagerCortxCmd):
    ha_ccm: Optional[CortxClusterManager] = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        if CortxClusterManager:
            self.ha_ccm = CortxClusterManager()
        else:
            raise RuntimeError('No cortx HA python API available')

    def cluster_status(self):
        ret = self.ha_ccm.cluster_controller.status()
        return HAResponse(**ret)

    def cluster_stop(self):
        return self.ha_ccm.cluster_controller.stop()

    def cluster_standby(self):
        return self.ha_ccm.cluster_controller.standby()

    def cluster_start(self):
        return self.ha_ccm.cluster_controller.start()

    def cluster_unstandby(self):
        return self.ha_ccm.cluster_controller.unstandby()


class ClusterManagerBroker:
    _pcs = None
    _cortx_cmd = None
    _cortx_api = None

    @property
    def cm_pcs(self):
        if self._pcs is None:
            ClusterManagerBroker._pcs = ClusterManagerPCS()
        return self._pcs

    @property
    def cm_cortx_cmd(self):
        if self._cortx_cmd is None:
            try:
                run_subprocess_cmd(f"{CORTX_HA_TOOL} --help")
            except Exception as exc:
                logger.warning(
                    f"'cortx' tool is not usable, ignoring: '{exc}'"
                )
                ClusterManagerBroker._cortx_cmd = MISSED
            else:
                ClusterManagerBroker._cortx_cmd = ClusterManagerCortxCmd()

        return None if self._cortx_cmd is MISSED else self._cortx_cmd

    @property
    def cm_cortx_api(self):
        if self._cortx_api is None:
            try:
                ClusterManagerBroker._cortx_api = ClusterManagerCortxAPI()
            except Exception as exc:
                logger.warning(
                    f"CORTX HA python API is not usable, ignoring: '{exc}'"
                )
                ClusterManagerBroker._cortx_cmd = MISSED

        return None if self._cortx_cmd is MISSED else self._cortx_api

    @property
    def cm(self):
        return (self.cm_cortx_api or self.cm_cortx_cmd or self.cm_pcs)


cm_broker = ClusterManagerBroker()


def is_cluster_healthy():
    """
    Wrapper over API of the Cortx Ha which provides the capability to check
    the health status of cluster.

    Raises
    ------
    NoMoreTriesError
        raise this exception if the number of tries was exceeded
    """
    logger.debug("Checking the CORTX cluster health")
    # FIXME switch to cortx interfaces once they are delivered
    try:
        ensure(cm_broker.cm_pcs.is_online, tries=1)
    except errors.NoMoreTriesError:
        return False
    else:
        return True


def cluster_stop():
    """
    Wrapper over HA interface to stop the cluster

    Raises
    ------
    NoMoreTriesError
        raise this exception if the number of tries was exceeded

    """
    logger.debug("Stopping the CORTX cluster")
    cm_broker.cm.cluster_stop()
    # NOTE: In new HA API cluster stop command is async.
    # So ensure block is added
    # FIXME switch to cortx interfaces once they are delivered
    ensure(cm_broker.cm_pcs.is_offline, tries=20, wait=10)


def cluster_standby():
    """
    Wrapper over HA interface to standby the cluster

    Raises
    ------
    NoMoreTriesError
        raise this exception if the number of tries was exceeded

    """
    logger.debug("Stopping the CORTX cluster health")
    cm_broker.cm.cluster_standby()
    ensure(cm_broker.cm.is_standby, tries=20, wait=10)


def cluster_start():
    """
    Wrapper over HA interface to start the cluster

    Raises
    ------
    NoMoreTriesError
        raise this exception if the number of tries was exceeded

    """
    logger.debug("Stopping the CORTX cluster health")
    cm_broker.cm.cluster_start()

    def _check():
        # TODO might be not accurate for some business logic
        return cm_broker.cm.is_standby() or cm_broker.cm.is_online()

    # FIXME switch to cortx interfaces once they are delivered
    ensure(_check, tries=20, wait=10)


def cluster_unstandby():
    """
    Wrapper over HA interface to unstandby the cluster

    Raises
    ------
    NoMoreTriesError
        raise this exception if the number of tries was exceeded

    """
    logger.debug("Stopping the CORTX cluster health")
    cm_broker.cm.cluster_unstandby()
    ensure(cm_broker.cm.is_online, tries=20, wait=10)
