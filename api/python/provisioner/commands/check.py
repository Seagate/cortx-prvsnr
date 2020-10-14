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
from typing import Type, Union

from . import RunArgs, CommandParserFillerMixin
from .. import inputs
from .. import config as cfg, values
from ..errors import SaltCmdResultError
from ..pillar import KeyPath, PillarKey, PillarResolver
from ..salt import local_minion_id, function_run
from ..vendor import attr


SRVNODE1 = "srvnode-1"
SRVNODE2 = "srvnode-2"

PENDING_SERVERS = frozenset({SRVNODE1, SRVNODE2})  # to make constant immutable


@attr.s(auto_attribs=True)
class CheckArgs:
    check_name: str = attr.ib(
        metadata={
            # TODO: need to output the full list of supported checks
            inputs.METADATA_ARGPARSER: {
                'help': "name of check/validation alias"
            }
        }
    )
    check_args: str = attr.ib(
        metadata={
            # TODO: maybe we need to create scheme for all checks with
            #  supported parameters. I think arguments should be independent
            #  of particular check/validation
            inputs.METADATA_ARGPARSER: {
                'help': ("optional arguments and parameters for "
                         "particular check")
            }
        },
        default=""  # empty string
    )

    targets: str = RunArgs.targets
    dry_run: bool = RunArgs.dry_run


@attr.s(auto_attribs=True)
class Check(CommandParserFillerMixin):
    """
    Base class for system and system components health and status validation
    """

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = CheckArgs

    _PRV_METHOD_MOD = "_"  # private method modificator
    # -c 1 means count of sending ECHO_REQUEST packets
    # -W 1 means timeout to wait for a response
    _PING_CMD_TMP = "ping -c 1 -W 1 {server_addr}"  # ping command template
    _BMC_CHECK_CMD = 'ipmitool chassis status | grep "System Power"'
    _CLUSTER_STATUS_CHECK_CMD = "pcs status --full cluster"
    _LOGS_ARE_GOOD_CHECK_CMD_TMP = ('test -f {log_filename} && '
                                    'grep -i "{key_phrase}" {log_filename} '
                                    '1>/dev/null && exit 1')
    _PSWDLESS_SSH_CHECK_CMD_TMP = ('ssh -o BatchMode=yes '
                                   '-o PasswordAuthentication=no '
                                   '{user}@{hostname} exit &>/dev/null '
                                   '&& test $? == 0 || exit 1')

    @staticmethod
    def _network(*, args: str, targets: str, dry_run: bool = False) -> dict:
        """
        Private method for network checks.

        :param args: network specific checking parameters and arguments
        :param targets: target nodes where network checks will be executed
        :param bool dry_run: for debugging purposes. Execute method without
                             real command execution on target nodes
        :return:
        """
        if dry_run:
            return dict()

        res = dict()

        minion_id = local_minion_id()

        cluster_path = KeyPath('cluster')
        node_network_path = KeyPath(f'cluster/{minion_id}/network/data_nw')

        pillar_keys = (PillarKey(cluster_path / 'type'),
                       PillarKey(node_network_path / "public_ip_addr"),
                       PillarKey(node_network_path / "pvt_ip_addr"),
                       PillarKey(cluster_path / "cluster_ip"))

        # maybe we need to call it from the all targets and analyze the output
        # from each node
        pillar = PillarResolver(cfg.LOCAL_MINION).get(pillar_keys)

        pillar = pillar.get(local_minion_id())  # type: dict

        for key in pillar_keys:
            if not pillar[key] or pillar[key] is values.MISSED:
                res[str(key.keypath)] = (f'{cfg.CheckVerdict.FAIL.value}: '
                                         'value is not specified')
            elif pillar[key] is None:
                res[str(key.keypath)] = (f'{cfg.CheckVerdict.FAIL.value}: '
                                         'value is unset')
            else:
                res[str(key.keypath)] = cfg.CheckVerdict.PASSED.value

        return res

    @staticmethod
    def _communicability(*, args: str, targets: str = cfg.ALL_MINIONS,
                         dry_run: bool = False) -> dict:
        """
        Check if nodes can communicate using `salt test.ping`

        :param args: bmc accessibility check specific parameters and arguments
        :param targets: target nodes where network checks will be executed
        :param dry_run: Execute method without real check execution on
                        target nodes
        :return:
        """
        if dry_run:
            return dict()

        res = dict()

        minion_id = local_minion_id()
        try:
            _res = function_run("test.ping", targets=minion_id)
            # TODO: parse response
            res[local_minion_id()] = (f"{cfg.CheckVerdict.PASSED.value}: "
                                      f"{str(_res)}")
        except SaltCmdResultError as e:
            res[minion_id] = f"{cfg.CheckVerdict.FAIL.value}: {str(e)}"

        return res

    def _bmc_accessibility(self, *, args: str, targets: str = cfg.ALL_MINIONS,
                           dry_run: bool = False) -> dict:
        """
        Check BMC accessibility

        :param args: bmc accessibility check specific parameters and arguments
        :param targets: target nodes where network checks will be executed
        :param dry_run: Execute method without real check execution on
                        target nodes
        :return:
        """
        if dry_run:
            return dict()

        res = dict()
        minion_id = local_minion_id()
        try:
            _res = function_run("cmd.run", targets=minion_id,
                                fun_args=[self._BMC_CHECK_CMD],
                                fun_kwargs=dict(python_shell=True))
            # TODO: parse command output if necessary
            res[minion_id] = f"{cfg.CheckVerdict.PASSED}: {str(_res)}"
        except SaltCmdResultError as e:
            res[minion_id] = f"{cfg.CheckVerdict.FAIL.value}: {str(e)}"

        return res

    def _connectivity(self, *, args: str,
                      servers: Union[list, tuple, set] = PENDING_SERVERS,
                      dry_run: bool = False) -> dict:
        """
        Check servers connectivity. Ping servers to check for availability

        :param str args: possible arguments for connectivity checks
        :param Union[list, tuple, set] servers: servers for pinging
        :param dry_run: Execute method without real check execution on
                        target nodes
        :return:
        """
        if dry_run:
            return dict()

        res = dict()
        for addr in servers:
            # NOTE: check ping of 'srvnode-2' from 'srvnode-1'
            # and vise versa
            # TODO: which targets do we need to use? Because we need to
            #  check cross connectivity if nodes > 2
            targets = set(servers) - {addr}
            targets = (cfg.LOCAL_MINION if not targets
                       else next(iter(targets)))  # takes just one node

            cmd = self._PING_CMD_TMP.format(server_addr=addr)
            try:
                function_run("cmd.run", targets=targets, fun_args=[cmd])
            except SaltCmdResultError:
                res[targets] = (f"{cfg.CheckVerdict.FAIL.value}: "
                                f"{addr} is not reachable from {targets}")
            else:
                res[targets] = cfg.CheckVerdict.PASSED.value

    def _logs_are_good(self, *, args: str, targets: str = cfg.ALL_MINIONS,
                       dry_run: bool = False) -> dict:
        """
        Check that logs are clear and don't contain some specific key phrases
        which signal about serious issues

        :param args: logs_are_good check specific parameters and arguments
        :param targets: target nodes where network checks will be executed
        :param dry_run: Execute method without real check execution on
                        target nodes
        :return:
        """
        def check_log_file(log_file, key_phrases, _targets):
            """
            Check separate log_file against key_phrases

            :param log_file:
            :param key_phrases:
            :param _targets
            :return:
            """
            for phrase in key_phrases:
                cmd = self._LOGS_ARE_GOOD_CHECK_CMD_TMP.format(
                    log_filename=log_file,
                    key_phrase=phrase)
                try:
                    function_run("cmd.run", targets=_targets, fun_args=[cmd])
                    res[minion_id] = {
                        log_file: f"{cfg.CheckVerdict.PASSED}"
                    }
                except SaltCmdResultError as e:
                    res[minion_id] = {
                        log_file: f"{cfg.CheckVerdict.FAIL}: {str(e)}"
                    }

        # grep "unable to stop resource" /var/log/pacemaker.log
        # grep "reboot" /var/log/corosync.log
        # grep "error" /var/log/corosync.log"

        if dry_run:
            return dict()

        res = dict()
        # they should be a constants
        corosync_log = "/var/log/cluster/corosync.log"
        pacemaker_log = "/var/log/pacemaker.log"

        corosync_key_phrases = (
            "reboot",
            "error"
        )
        pacemaker_key_phrases = (
            "unable to stop resource"
        )

        minion_id = local_minion_id()

        check_log_file(corosync_log, corosync_key_phrases, minion_id)
        check_log_file(pacemaker_log, pacemaker_key_phrases, minion_id)

        return res

    def _passwordless_ssh_access(
                        self, *, args: str,
                        servers: Union[list, tuple, set] = PENDING_SERVERS,
                        dry_run: bool = False) -> dict:
        """

        :param args: passwordless ssh access check specific parameters
                     and arguments
        :param servers: servers for checking passwordless SSH
        :param dry_run: Execute method without real check execution on
                        target nodes

        :return:
        """
        # NOTE: the logic is similar to `_connectivity` method
        if dry_run:
            return dict()

        res = dict()
        for addr in servers:
            # NOTE: check ping of 'srvnode-2' from 'srvnode-1'
            # and vise versa
            # TODO: which targets do we need to use? Because we need to
            #  check cross connectivity if nodes > 2
            targets = set(servers) - {addr}

            targets = (cfg.LOCAL_MINION if not targets
                       else next(iter(targets)))  # takes just one node

            cmd = self._PSWDLESS_SSH_CHECK_CMD_TMP.format(user='root',
                                                          hostname=addr)
            try:
                function_run("cmd.run", targets=targets, fun_args=[cmd])
            except SaltCmdResultError:
                res[targets] = (f"{cfg.CheckVerdict.FAIL.value}: "
                                f"'{addr}' is not reachable from {targets}")
            else:
                res[targets] = cfg.CheckVerdict.PASSED.value

    def _cluster_status(self, *, args: str, targets: str = cfg.ALL_MINIONS,
                        dry_run: bool = False) -> dict:
        """
        Check cluster status

        :param args: cluster_status check specific parameters and arguments
        :param targets: target nodes where network checks will be executed
        :param dry_run: Execute method without real check execution on
                        target nodes
        :return:
        """
        if dry_run:
            return dict()

        res = dict()

        minion_id = local_minion_id()
        try:
            _res = function_run("cmd.run", targets=minion_id,
                                fun_args=[self._CLUSTER_STATUS_CHECK_CMD])
            # TODO: parse command if necessary
            res[minion_id] = f"{cfg.CheckVerdict.PASSED.value}: {str(_res)}"
        except SaltCmdResultError as e:
            res[minion_id] = f"{cfg.CheckVerdict.FAIL.value}: {str(e)}"

        return res

    def check_all(self, check_args: str = "", targets: str = cfg.ALL_MINIONS,
                  dry_run: bool = False) -> dict:
        """
        Run all checks which are available and supported

        :param str check_args: check specific arguments
        :param str targets: target nodes where checks are planned
                            to be executed
        :param bool dry_run: for debugging purposes. Execute method without
                             real check execution on target nodes
        :return:
        """
        res = dict()
        for check_name in cfg.CHECKS:
            _res = getattr(self,
                           self._PRV_METHOD_MOD + check_name)(args=check_args,
                                                              targets=targets,
                                                              dry_run=dry_run)
            res[check_name] = _res  # aggregate result to simple dict form

        return res

    def run(self, check_name: cfg.Checks, check_args: str = "",
            targets: str = cfg.ALL_MINIONS, dry_run: bool = False) -> dict:
        """
        Basic run method to execute remote commands on targets nodes:

        :param str check_name: specific command to be executed on target nodes
        :param str check_args: check specific arguments
        :param str targets: target nodes where checks are planned
                            to be executed
        :param bool dry_run: for debugging purposes. Execute method without
                             real check execution on target nodes
        :return:
        """
        check_name = check_name.strip().lower()

        res = dict()
        if check_name in cfg.CHECKS:
            _res = getattr(self,
                           self._PRV_METHOD_MOD + check_name)(args=check_args,
                                                              targets=targets,
                                                              dry_run=dry_run)
            res[check_name] = _res  # aggregate result to simple dict form
        else:
            raise ValueError(f'Check "{check_name}" is not supported')

        return res
