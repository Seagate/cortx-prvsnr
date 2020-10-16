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
from ..hare import ensure_cluster_is_healthy
from ..pillar import KeyPath, PillarKey, PillarResolver
from ..salt import local_minion_id, function_run, cmd_run
from ..salt_minion import check_salt_minions_are_ready
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
        },
        default=None
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


@attr.s(auto_attribs=True)
class Check(CommandParserFillerMixin):
    """
    Base class for system and system components health and status validation
    """

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = CheckArgs

    _PRV_METHOD_MOD = "_"  # private method modificator

    @staticmethod
    def _network(*, args: str) -> dict:
        """
        Private method for network checks.

        :param args: network specific checking parameters and arguments
        :return:
        """
        res: dict = dict()

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
    def _communicability(
                *, args: str,
                targets: Union[list, tuple, set] = PENDING_SERVERS) -> dict:
        """
        Check if nodes can communicate using `salt test.ping`

        :param args: bmc accessibility check specific parameters and arguments
        :param targets: target nodes where network checks will be executed
        :return:
        """
        res: dict = dict()

        # TODO: need to resolve cfg.ALL_MINIONS alias
        #  to the list of minions
        # TODO: create check and return list of nodes which are down
        if check_salt_minions_are_ready(targets=targets):
            res[local_minion_id()] = cfg.CheckVerdict.PASSED.value
        else:
            res[local_minion_id()] = cfg.CheckVerdict.FAIL.value

        return res

    def _bmc_accessibility(self, *, args: str) -> dict:
        """
        Check BMC accessibility

        :param args: bmc accessibility check specific parameters and arguments
        :return:
        """
        _BMC_CHECK_CMD = 'ipmitool chassis status | grep "System Power"'

        res: dict = dict()

        minion_id = local_minion_id()

        try:
            _res = cmd_run(_BMC_CHECK_CMD, targets=minion_id,
                           fun_kwargs=dict(python_shell=True))
            # TODO: parse command output if necessary
            res[minion_id] = f"{cfg.CheckVerdict.PASSED}: {str(_res)}"
        except SaltCmdResultError as e:
            res[minion_id] = f"{cfg.CheckVerdict.FAIL.value}: {str(e)}"

        return res

    def _connectivity(self, *,
                      servers: Union[list, tuple, set] = PENDING_SERVERS,
                      args: str) -> dict:
        """
        Check servers connectivity. Ping servers to check for availability

        :param Union[list, tuple, set] servers: servers for pinging
        :param str args: possible arguments for connectivity checks
        :return:
        """
        # ping command template
        # -c 1 means count of sending ECHO_REQUEST packets
        # -W 1 means timeout to wait for a response
        _PING_CMD_TMPL = "ping -c 1 -W 1 {server_addr}"

        res: dict = dict()
        for addr in servers:
            # NOTE: check ping of 'srvnode-2' from 'srvnode-1'
            # and vise versa
            # TODO: which targets do we need to use? Because we need to
            #  check cross connectivity if nodes > 2 and all possible pairs
            targets = set(servers) - {addr}
            targets = (cfg.LOCAL_MINION if not targets
                       else next(iter(targets)))  # takes just one node

            cmd = _PING_CMD_TMPL.format(server_addr=addr)
            try:
                cmd_run(cmd, targets=targets)
            except SaltCmdResultError:
                res[targets] = (f"{cfg.CheckVerdict.FAIL.value}: "
                                f"{addr} is not reachable from {targets}")
            else:
                res[targets] = cfg.CheckVerdict.PASSED.value

        return res

    def _logs_are_good(self, *, args: str) -> dict:
        """
        Check that logs are clear and don't contain some specific key phrases
        which signal about serious issues

        :param args: logs_are_good check specific parameters and arguments
        :return:
        """
        # TODO: do we need to fail if logfile doesn't exist?
        _LOGS_ARE_GOOD_CHECK_CMD_TMPL = (
                                    'test -f {log_filename} || '
                                    '{{ echo "logfile does not exist" && '
                                    'exit 1 ; }} ; '
                                    'grep -i "{key_phrase}" {log_filename} '
                                    '1>/dev/null && '
                                    'echo "{key_phrase} exists in logfile" && '
                                    'exit 1')

        minion_id = local_minion_id()
        res: dict = {minion_id: dict()}

        def check_log_file(log_file, key_phrases, _targets):
            """
            Check separate log_file against key_phrases

            :param log_file:
            :param key_phrases:
            :param _targets
            :return:
            """
            for phrase in key_phrases:
                cmd = _LOGS_ARE_GOOD_CHECK_CMD_TMPL.format(
                    log_filename=log_file,
                    key_phrase=phrase)
                try:
                    cmd_run(cmd, targets=_targets)
                except SaltCmdResultError as e:
                    res[minion_id][log_file] = (
                                    f"{cfg.CheckVerdict.FAIL.value}: {str(e)}")
                    return

                res[minion_id][log_file] = cfg.CheckVerdict.PASSED.value

        # grep "unable to stop resource" /var/log/pacemaker.log
        # grep "reboot" /var/log/corosync.log
        # grep "error" /var/log/corosync.log"

        # they should be a constants
        corosync_log = "/var/log/cluster/corosync.log"
        pacemaker_log = "/var/log/pacemaker.log"

        corosync_key_phrases = (
            "reboot",
            "error"
        )
        pacemaker_key_phrases = (
            "unable to stop resource",
        )

        check_log_file(corosync_log, corosync_key_phrases, minion_id)
        check_log_file(pacemaker_log, pacemaker_key_phrases, minion_id)

        return res

    def _passwordless_ssh_access(
                        self, *,
                        servers: Union[list, tuple, set] = PENDING_SERVERS,
                        args: str) -> dict:
        """
        Check if passwordless SSH access is possible between nodes

        :param args: passwordless ssh access check specific parameters
                     and arguments
        :param servers: servers for checking passwordless SSH
        :return:
        """
        # NOTE: the logic is similar to `_connectivity` method
        _PSWDLESS_SSH_CHECK_CMD_TMPL = (
                                    'ssh -o BatchMode=yes '
                                    '-o PasswordAuthentication=no '
                                    '{user}@{hostname} exit 0 &>/dev/null; '
                                    'test $? == 0 || {{ echo "fail" && '
                                    'exit 1; }}')

        res: dict = dict()
        user = "root"
        for addr in servers:
            # NOTE: check ping of 'srvnode-2' from 'srvnode-1'
            # and vise versa
            # TODO: which targets do we need to use? Because we need to
            #  check cross connectivity if nodes > 2
            targets = set(servers) - {addr}

            targets = (cfg.LOCAL_MINION if not targets
                       else next(iter(targets)))  # takes just one node

            cmd = _PSWDLESS_SSH_CHECK_CMD_TMPL.format(user=user,
                                                      hostname=addr)
            try:
                _res = cmd_run(cmd, targets=targets)
            except SaltCmdResultError:
                res[targets] = (f"{cfg.CheckVerdict.FAIL.value}: "
                                f"'{addr}' is not reachable from {targets} "
                                f"under user {user}")
            else:
                res[targets] = cfg.CheckVerdict.PASSED.value

        return res

    def _cluster_status(self, *, args: str) -> dict:
        """
        Check cluster status

        :param args: cluster_status check specific parameters and arguments
        :return:
        """
        # NOTE: per my discussion with Andrey Kononykhin replace
        #  `pcs status --full cluster` and its complex parsing by existing
        #  ensure_cluster_is_healthy call
        res: dict = dict()

        try:
            ensure_cluster_is_healthy()
            res[local_minion_id()] = f"{cfg.CheckVerdict.PASSED.value}"
        except Exception:
            res[local_minion_id()] = f"{cfg.CheckVerdict.FAIL.value}"

        return res

    def run(self, check_name: cfg.Checks = None, check_args: str = "",
            targets: str = cfg.ALL_MINIONS) -> dict:
        """
        Basic run method to execute checks specified by `check_name` or
        perform all checks if `check_name` is omitted

        :param str check_name: specific command to be executed on target nodes
        :param str check_args: check specific arguments
        :param str targets: target nodes where checks are planned
                            to be executed
        :return:
        """
        res: dict = dict()

        if check_name is None:
            for check_name in cfg.CHECKS:
                _res = getattr(self,
                               self._PRV_METHOD_MOD + check_name)(
                                                            args=check_args)
                res[check_name] = _res  # aggregate result to simple dict form

        check_name = check_name.strip().lower()

        if check_name in cfg.CHECKS:
            _res = getattr(self,
                           self._PRV_METHOD_MOD + check_name)(args=check_args)

            res[check_name] = _res  # aggregate result to simple dict form

        else:
            raise ValueError(f'Check "{check_name}" is not supported')

        return res
