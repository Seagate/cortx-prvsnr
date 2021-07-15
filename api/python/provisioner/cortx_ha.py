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


class ClusterManagerBase:

    _name = None

    def _run_cmd(self, cmd: str, json=False):
        ret = cmd_run(cmd, targets=LOCAL_MINION)
        ret = next(iter(ret.values()))
        return load_json_str(ret) if json else ret

    def cluster_status(self) -> HAClusterStatus:
        """Return the status."""
        raise NotImplementedError

    def cluster_stop(self):
        """Stop the cluster."""
        raise NotImplementedError

    def cluster_standby(self):
        """Standby the cluster."""
        raise NotImplementedError

    def cluster_start(self):
        """Start the cluster."""
        raise NotImplementedError

    def cluster_unstandby(self):
        """Unstandby the cluster."""
        raise NotImplementedError

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
        return ret in status

    def is_offline(self):
        """Check whether cluster is offline."""
        return self.check_status(HAClusterStatus.OFFLINE)

    def is_online(self):
        """Check whether cluster is online."""
        return self.check_status(HAClusterStatus.ONLINE)

    def is_standby(self):
        """Check whether cluster is in standby."""
        return self.check_status(HAClusterStatus.STANDBY)


class ClusterManagerPCS(ClusterManagerBase):
    _name = 'pcs tool'

    def cluster_status(self) -> HAClusterStatus:
        try:
            res = self._run_cmd('pcs status')
        except errors.SaltCmdResultError as exc:
            if (
                'cluster is not currently running on this node'
                in str(exc.reason)
            ):
                return HAClusterStatus.OFFLINE
            else:
                logger.warning(f"Cluster status failed: {exc}")
                raise
        else:
            _res = res.lower()
            # TODO naive implementation
            if 'online:' in _res:
                return HAClusterStatus.ONLINE
            elif 'standby' in _res:
                return HAClusterStatus.STANDBY
            elif 'offline:' in _res:
                return HAClusterStatus.OFFLINE
            else:
                raise errors.ProvisionerError(
                    f"Unknown cluster status: '{res}'"
                )

    def cluster_stop(self):
        self._run_cmd(
            "pcs cluster stop --all --force"
        )

    def cluster_standby(self):
        self._run_cmd(
            "pcs cluster standby --all"
        )

    def cluster_start(self):
        self._run_cmd('pcs cluster start --all')

    def cluster_unstandby(self):
        self._run_cmd('pcs cluster unstandby --all')


def converter_str_lower(value: str):
    return value.lower()


@attr.s(auto_attribs=True)
class HAResponse:

    status: str = attr.ib(converter=converter_str_lower)
    output: str
    error: str

    @classmethod
    def from_raw(cls, raw: str):
        res = load_json_str(raw)
        _res = dict(
            status=res.get('status'),
            # Note. comptibility with older versions of Cortx HA
            output=res.get('output', res.get('msg')),
            # Note. compatibility as well - error could be missed
            #       in older versions
            error=res.get('error', '')
        )

        not_found = [k for k, v in _res.items() if v is None]

        if not_found:
            raise ValueError(
                f"'{not_found}' keys are missed in Cortx HA response '{raw}'"
            )

        ret = cls(**_res)
        try:
            HACmdResult(ret.status)
        except ValueError:
            logger.warning(
                f"unexpected Cortx HA response status '{res['status']}'"
            )

        return ret


class ClusterManagerCortxBase(ClusterManagerBase):

    @staticmethod
    def parse_ret(ret: str) -> HAResponse:
        resp = HAResponse.from_raw(ret)
        if resp.status == HACmdResult.FAILED.value:
            error = resp.error or resp.output
            if 'is not implemented' in error.lower():
                raise NotImplementedError(error)

            raise errors.ProvisionerError(
                f"HA command failed with error: '{error}'"
            )
        return resp

    def _run_api(self, api: str):
        raise NotImplementedError

    def cluster_status(self) -> HAClusterStatus:
        status = self._run_api('status')
        return HAClusterStatus(status.output)

    def cluster_stop(self):
        self._run_api('stop')

    def cluster_standby(self):
        self._run_api('standby')

    def cluster_start(self):
        self._run_api('start')

    def cluster_unstandby(self):
        self._run_api('unstandby')


class ClusterManagerCortxCmd(ClusterManagerCortxBase):
    _name = 'cortx tool'

    def _run_api(self, api: str):
        ret = self._run_cmd(f"{CORTX_HA_TOOL} cluster {api}", json=True)
        return self.parse_ret(ret)

    def cluster_status(self):
        raise NotImplementedError(
            f"'status' is not supported by '{CORTX_HA_TOOL}' tool"
        )

    def cluster_standby(self):
        raise NotImplementedError(
            f"'standby' is not supported by '{CORTX_HA_TOOL}' tool"
        )

    def cluster_unstandby(self):
        raise NotImplementedError(
            f"'unstandby' is not supported by '{CORTX_HA_TOOL}' tool"
        )


def _call_ha_api_carefully(api):
    def _ha_api_wrapper(*args, **kwargs):
        try:
            return api(*args, **kwargs)
        except AttributeError:
            raise NotImplementedError(
                f"'{api}' api is not available in HA python API yet"
            )
    return _ha_api_wrapper


@attr.s(auto_attribs=True)
class ClusterManagerCortxAPI(ClusterManagerCortxBase):
    _name = 'Cortx HA python API'

    ha_ccm: Optional[CortxClusterManager] = attr.ib(init=False, default=None)

    def __attrs_post_init__(self):
        if CortxClusterManager:
            self.ha_ccm = CortxClusterManager()
        else:
            raise RuntimeError('No cortx HA python API available')

    def _run_api(self, api: str):
        ret = getattr(self.ha_ccm.cluster_controller, api)()
        return self.parse_ret(ret)

    @_call_ha_api_carefully
    def cluster_status(self) -> HAClusterStatus:
        return super().cluster_status()

    @_call_ha_api_carefully
    def cluster_standby(self):
        super().cluster_standby()

    @_call_ha_api_carefully
    def cluster_unstandby(self):
        super().cluster_unstandby()

    @_call_ha_api_carefully
    def cluster_start(self):
        super().cluster_start()


class ClusterManagerBroker(ClusterManagerBase):
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
    def active_interfaces(self):
        return [
            i
            for i in (self.cm_cortx_api, self.cm_cortx_cmd, self.cm_pcs)
            if i
        ]

    def _delegate(self, api, *args, **kwargs):
        ha_api = self.active_interfaces

        if not ha_api:
            raise errors.ProvisionerError("no active HA interfaces found")

        for cm in ha_api:
            try:
                return getattr(cm, api)(*args, **kwargs)
            except NotImplementedError:
                pass

        raise NotImplementedError(
            f"'{api}' is not supported by any of {[i._name for i in ha_api]}"
        )

    def __init__(self):
        def _api_wrapper(api):
            def _api_f(*args, **kwargs):
                return self._delegate(api, *args, **kwargs)
            return _api_f

        # TODO make that dynamic
        for api in (
            'cluster_status',
            'cluster_stop',
            'cluster_standby',
            'cluster_start',
            'cluster_unstandby',
            'is_offline',
            'is_online'
        ):
            setattr(self, api, _api_wrapper(api))


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
    try:
        ensure(cm_broker.is_online, tries=1)
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
    cm_broker.cluster_stop()
    # NOTE: In new HA API cluster stop command is async.
    # So ensure block is added
    ensure(cm_broker.is_offline, tries=20, wait=10)


def cluster_standby():
    """
    Wrapper over HA interface to standby the cluster

    Raises
    ------
    NoMoreTriesError
        raise this exception if the number of tries was exceeded

    """
    logger.debug("Stopping the CORTX cluster health")
    cm_broker.cluster_standby()
    ensure(cm_broker.is_standby, tries=20, wait=10)


def cluster_start():
    """
    Wrapper over HA interface to start the cluster

    Raises
    ------
    NoMoreTriesError
        raise this exception if the number of tries was exceeded

    """
    logger.debug("Stopping the CORTX cluster health")
    cm_broker.cluster_start()

    def _check():
        # TODO might be not accurate for some business logic
        return cm_broker.check_status(
            (
                HAClusterStatus.STANDBY,
                HAClusterStatus.ONLINE
            )
        )

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
    cm_broker.cluster_unstandby()
    ensure(cm_broker.is_online, tries=20, wait=10)
