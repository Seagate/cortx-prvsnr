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
from typing import Type, Union, List
import json

from . import CommandParserFillerMixin
from .. import inputs
from .. import config as cfg, values
from ..errors import SaltCmdResultError
from ..hare import ensure_cluster_is_healthy
from ..pillar import KeyPath, PillarKey, PillarResolver
from ..salt import local_minion_id, cmd_run
from ..salt_minion import check_salt_minions_are_ready
from ..vendor import attr


SRVNODE1 = "srvnode-1"
SRVNODE2 = "srvnode-2"

PENDING_SERVERS = frozenset({SRVNODE1, SRVNODE2})  # to make constant immutable


class CheckEntry:

    """Result of the single validation"""

    def __init__(self, check_name: str):
        """
        Setup check
        Args:
            str check_name: check/validation name or label
        """
        self._check_name = check_name
        self._verdict = None
        self._comment = None
        self._target = None

    def __str__(self):
        """String representation of the single check"""
        if self.is_set:
            if self._comment:
                return (f"{self._target}: {self._check_name}: "
                        f"{self._verdict.value}: {self._comment}")

            return (f"{self._target}: {self._check_name}: "
                    f"{self._verdict.value}")

        return ""  # We can return just None value

    def to_dict(self) -> dict:
        """
        Return dict representation of check
        Returns:

        """
        if self.is_set:
            if self._comment:
                return {self._check_name: f"{self._target}:"
                                          f"{self._verdict.value}: "
                                          f"{self._comment}"}
            return {self._check_name: f"{self._target}: {self._verdict.value}"}

        return dict()

    def set_fail(self, *, target: str, comment: str = ""):
        """
        Set fail for the check
        Args:
            str target: target where validation was run
            str comment: validation result comment (reason of fail)

        Returns:

        """
        self._verdict = cfg.CheckVerdict.FAIL
        self._target = target
        self._comment = comment

    def set_passed(self, *, target, comment: str = ""):
        """
        Set passed for the check
        Args:
            str target: target where validation was run
            str comment: validation result comment (optional)
        Returns:

        """
        self._verdict = cfg.CheckVerdict.PASSED
        self._target = target
        self._comment = comment

    @property
    def is_passed(self) -> bool:
        """
        Returns: True if check is passed and False otherwise

        """
        return self._verdict == cfg.CheckVerdict.PASSED

    @property
    def is_failed(self) -> bool:
        """

        Returns: True if check is failed and False otherwise

        """
        return self._verdict == cfg.CheckVerdict.FAIL

    @property
    def is_set(self) -> bool:
        """
        Validates if self._verdict is set up to one of the CheckVerdict values
        Returns:

        """
        return self._verdict is not None


class CheckResult:

    """Base class to represent check/validation result"""

    def __init__(self):
        self._check_entries: list = list()

    def __iter__(self):
        """
        Iterate over all check results

        Returns:

        Example:

            ...

            check_results = CheckResult()
            for check in check_results:
                do_something(check)

            ...

        """
        for check in self._check_entries:
            yield check

    def __str__(self):
        """String representation of all checks"""
        # return str(self.to_dict())
        # TODO: maybe it is better to use json.dump
        return json.dumps(self.to_dict(), indent=4)

    @property
    def is_passed(self) -> bool:
        """
        Verifies if all checks are passed

        Returns: True if all checks are passed and False otherwise

        """
        return all(check.is_passed for check in self._check_entries)

    @property
    def is_failed(self) -> bool:
        """
        Verifies if at least one check is failed
        Returns: True if at least one check is failed and False otherwise

        """
        return any(check.is_failed for check in self._check_entries)

    def add_checks(self, check: Union[CheckEntry, List[CheckEntry]]) -> None:
        """
        Add check entry to the check entries chain

        Args:
            CheckEntry check: check entry(ies) with single check result

        Returns:

        """
        def _add_check(check_entry: CheckEntry):
            if check_entry.is_set:
                self._check_entries.append(check_entry)
            else:
                raise ValueError("Check verdict is not set")

        if isinstance(check, list):
            for _check in check:
                _add_check(_check)
        else:
            _add_check(check)

    def get_passed(self) -> list:
        """
        Return all check entries which passed
        Returns: list with all passed checks

        """
        return [check for check in self._check_entries if check.is_passed]

    def get_failed(self) -> list:
        """
        Return all check entries which failed
        Returns: list with all failed checks

        """
        return [check for check in self._check_entries if check.is_failed]

    def to_dict(self) -> dict:
        """
        Return dictionary representation of check results
        Returns:

        """
        result = dict()

        for check in self._check_entries:
            for key, value in check.to_dict().items():
                if key in result:
                    if isinstance(result[key], list):
                        result[key].append(value)
                    else:
                        result[key] = [result[key], value]
                else:
                    result[key] = value

        return result


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
    def _network(*, args: str) -> List[CheckEntry]:
        """
        Private method for network checks.

        :param args: network specific checking parameters and arguments
        :return:
        """
        res: List[CheckEntry] = list()

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
            _res = CheckEntry(cfg.Checks.NETWORK.value)
            if not pillar[key] or pillar[key] is values.MISSED:
                _res.set_fail(target=str(key.keypath),
                              comment="value is not specified")
            elif pillar[key] is None:
                _res.set_fail(target=str(key.keypath),
                              comment="value is unset")
            else:
                _res.set_passed(target=str(key.keypath))

            res.append(_res)

        return res

    @staticmethod
    def _communicability(
            *, args: str,
            targets: Union[list, tuple, set] = PENDING_SERVERS) -> CheckEntry:
        """
        Check if nodes can communicate using `salt test.ping`

        :param args: bmc accessibility check specific parameters and arguments
        :param targets: target nodes where network checks will be executed
        :return:
        """
        res: CheckEntry = CheckEntry(cfg.Checks.COMMUNICABILITY.value)

        # TODO: need to resolve cfg.ALL_MINIONS alias
        #  to the list of minions
        # TODO: create check and return list of nodes which are down
        if check_salt_minions_are_ready(targets=targets):
            res.set_passed(target=local_minion_id())
        else:
            res.set_fail(target=local_minion_id())

        return res

    @staticmethod
    def _bmc_accessibility(*, args: str) -> CheckEntry:
        """
        Check BMC accessibility

        :param args: bmc accessibility check specific parameters and arguments
        :return:
        """
        _BMC_CHECK_CMD = 'ipmitool chassis status | grep "System Power"'

        res: CheckEntry = CheckEntry(cfg.Checks.BMC_ACCESSIBILITY.value)

        minion_id = local_minion_id()

        try:
            _res = cmd_run(_BMC_CHECK_CMD, targets=minion_id,
                           fun_kwargs=dict(python_shell=True))
            # TODO: parse command output if necessary
            res.set_passed(target=minion_id, comment=str(_res))
        except SaltCmdResultError as e:
            res.set_fail(target=minion_id, comment=str(e))

        return res

    @staticmethod
    def _connectivity(*, servers: Union[list, tuple, set] = PENDING_SERVERS,
                      args: str) -> CheckEntry:
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

        res: CheckEntry = CheckEntry(cfg.Checks.CONNECTIVITY.value)

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
                res.set_fail(target=targets,
                             comment=(f"{cfg.CheckVerdict.FAIL.value}: {addr} "
                                      f"is not reachable from {targets}"))
            else:
                res.set_passed(target=targets)

        return res

    @staticmethod
    def _logs_are_good(*, args: str) -> List[CheckEntry]:
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
        res: List[CheckEntry] = list()

        def check_log_file(log_file, key_phrases, _targets):
            """
            Check separate log_file against key_phrases

            :param log_file:
            :param key_phrases:
            :param _targets
            :return:
            """
            _res: CheckEntry = CheckEntry(cfg.Checks.LOGS_ARE_GOOD.value)
            for phrase in key_phrases:
                cmd = _LOGS_ARE_GOOD_CHECK_CMD_TMPL.format(
                    log_filename=log_file,
                    key_phrase=phrase)
                try:
                    cmd_run(cmd, targets=_targets)
                except SaltCmdResultError as e:
                    _res.set_fail(target=minion_id,
                                  comment=f"{log_file}: {str(e)}")
                    return _res

            _res.set_passed(target=minion_id, comment=f"{log_file}")

            return _res

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

        res.append(
            check_log_file(corosync_log, corosync_key_phrases, minion_id))
        res.append(
            check_log_file(pacemaker_log, pacemaker_key_phrases, minion_id))

        return res

    @staticmethod
    def _passwordless_ssh_access(
                            *,
                            servers: Union[list, tuple, set] = PENDING_SERVERS,
                            args: str) -> CheckEntry:
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

        res: CheckEntry = CheckEntry(cfg.Checks.PASSWORDLESS_SSH_ACCESS.value)

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
                res.set_fail(target=targets,
                             comment=(f"{cfg.CheckVerdict.FAIL.value}: "
                                      f"'{addr}' is not reachable from "
                                      f"{targets} under user {user}"))
            else:
                res.set_passed(target=targets)

        return res

    @staticmethod
    def _cluster_status(*, args: str) -> CheckEntry:
        """
        Check cluster status

        :param args: cluster_status check specific parameters and arguments
        :return:
        """
        # NOTE: per my discussion with Andrey Kononykhin replace
        #  `pcs status --full cluster` and its complex parsing by existing
        #  ensure_cluster_is_healthy call
        res: CheckEntry = CheckEntry(cfg.Checks.CLUSTER_STATUS.value)

        try:
            ensure_cluster_is_healthy()
            res.set_passed(target=local_minion_id())
        except Exception:
            res.set_fail(target=local_minion_id())

        return res

    def run(self, check_name: cfg.Checks = None, check_args: str = "",
            targets: str = cfg.ALL_MINIONS) -> CheckResult:
        """
        Basic run method to execute checks specified by `check_name` or
        perform all checks if `check_name` is omitted

        :param str check_name: specific command to be executed on target nodes
        :param str check_args: check specific arguments
        :param str targets: target nodes where checks are planned
                            to be executed
        :return:
        """
        res: CheckResult = CheckResult()

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

            res.add_checks(_res)  # aggregate all check results

        else:
            raise ValueError(f'Check "{check_name}" is not supported')

        return res
