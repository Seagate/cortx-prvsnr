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
from typing import Type, Union, List, Optional, Any
import json

from provisioner import salt
from provisioner.commands.validator.validator import CompatibilityValidator

from ._basic import CommandParserFillerMixin
from .. import inputs
from .. import config as cfg, values
from ..errors import (
    SaltCmdResultError,
    ValidationError,
    CriticalValidationError,
    SWUpgradeError)
from ..hare import ensure_cluster_is_healthy
from ..pillar import KeyPath, PillarKey, PillarResolver
from ..salt import local_minion_id, cmd_run
from ..salt_minion import check_salt_minions_are_ready
from ..vendor import attr

logger = logging.getLogger(__name__)

cortx_py_utils_import_error = False
try:
    from cortx.utils.validator.v_network import NetworkV
    from cortx.utils.validator.v_storage import StorageV
    from cortx.utils.validator.v_bmc import BmcV
except ImportError:
    cortx_py_utils_import_error = True


SRVNODE1 = "srvnode-1"
SRVNODE2 = "srvnode-2"

PENDING_SERVERS = frozenset({SRVNODE1, SRVNODE2})  # to make constant immutable


# TODO IMPROVEMENT: Classes and its methods for `CheckEntry` and `CheckResult`
#  should be covered by basic unit tests
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
        self.checked_target = None
        self._critical = None  # mark that check is critical

    def __str__(self):
        """String representation of the single check"""
        if self.is_set:
            if self._comment:
                return (f"{self.checked_target}: {self._check_name}: "
                        f"{self._verdict.value}: {self._comment}")

            return (f"{self.checked_target}: {self._check_name}: "
                    f"{self._verdict.value}")

        return ""  # We can return just None value

    def to_dict(self) -> dict:
        """
        Return dict representation of check
        Returns:

        """
        if self.is_set:
            if self._comment:
                return {self._check_name: f"{self.checked_target}: "
                                          f"{self._verdict.value}: "
                                          f"{self._comment}"}
            return {
                self._check_name:
                    f"{self.checked_target}: {self._verdict.value}"}

        return dict()

    def set_fail(self, *, checked_target: str, comment: str = ""):
        """
        Set fail for the check
        Args:
            str target: checked_target where validation was run
            str comment: validation result comment (reason of fail)

        Returns:

        """
        self._verdict = cfg.CheckVerdict.FAIL
        self.checked_target = checked_target
        self._comment = comment

    def set_passed(self, *, checked_target, comment: str = ""):
        """
        Set passed for the check
        Args:
            str checked_target: target where validation was run
            str comment: validation result comment (optional)
        Returns:

        """
        self._verdict = cfg.CheckVerdict.PASSED
        self.checked_target = checked_target
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

    @property
    def is_critical(self) -> bool:
        """
        Return True if check result is marked as critical and False otherwise
        """
        return bool(self._critical)

    @property
    def check_name(self):
        """

        :return:
        """
        return self._check_name

    def set_critical(self, critical: bool) -> None:
        """
        Mark that check result is critical (belongs to critical validation)

        :param bool critical: value to mark the check result as critical or
                              non-critical
        :return:
        """
        self._critical = critical


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

    @property
    def has_critical_failure(self) -> bool:
        """
        Verify if at lease one critical check is failed
        NOTE: self.is_failed is not equal to self.has_critical_failure

        :return: True if at least one critical error failed and False otherwise
        """
        return any(check.is_failed and check.is_critical
                   for check in self._check_entries)

    def add_checks(self, check: Union[CheckEntry, List[CheckEntry]],
                   critical: bool = False) -> None:
        """
        Add check entry to the check entries chain

        Args:
            CheckEntry check: check entry(ies) with single check result

        Returns:

        """
        def _add_check(check_entry: CheckEntry):
            if check_entry.is_set:
                check_entry.set_critical(critical)
                self._check_entries.append(check_entry)
            else:
                raise ValueError("Check verdict is not set")

        if isinstance(check, list):
            for _check in check:
                _add_check(_check)
        else:
            _add_check(check)

    def get_checks(self, *, failed: Optional[bool] = None,
                   critical: Optional[bool] = None) -> List[CheckEntry]:
        """
        Return check entries that satisfying the given parameters.
        If both parameters ``failed`` and ``critical`` are ``None``,
        the function returns all checks. Otherwise, it returns check entries,
        which satisfy either one or both parameters.

        :param Optional[bool] failed: parameter to filter check results by
                                      failed value
        :param Optional[bool] critical: parameter to filter returning check
                                        results by the critical value

        :return: check entries selected on the given parameters
                 Note: it can return passed and failed checks together

        Examples:
            Get all passed check entries (both critical and non-critical):
                ``check_result.get_checks(failed=False)``
            Get all critical failed check entries:
                ``check_result.get_checks(failed=True, critical=True)``
            Get all check entries added to `CheckResult` instance:
                ``check_result.get_checks()``
        """
        def _in(left: Union[str, int, float, bool],
                right: Union[set, list, tuple, str]) -> bool:
            return left in right

        def _and(*args: Any) -> bool:
            return all(args)

        bool_values = {False, True}
        critical_values = bool_values if critical is None else {critical}
        failed_values = bool_values if failed is None else {failed}

        return [check for check in self._check_entries
                if _and(_in(check.is_failed, failed_values),
                        _in(check.is_critical, critical_values))]

    def get_by_name(self, *check_names: str) -> list:
        """
        Return group of check entries by its names

        Usage:
            check_result.get_by_name("hostnames")
            check_result.get_by_name("cluster_status", "network",
                                     "logs_are_good")

        :param check_names: single check name or list of check names
        :return: list (can be empty) of check entries
                 with requested check names
        """
        return [check_entry for check_entry in self._check_entries
                if check_entry.check_name in check_names]

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


class DecisionMaker:

    """Basic Decision Maker class.
    """

    @staticmethod
    def format_checks(*check_entries: CheckEntry) -> str:
        """
        Format all passed check entries to a single string

        :param CheckEntry check_entries: one or more CheckEntry objects

        :return: string representation of all passed check entries
        """
        return "; ".join(str(check) for check in check_entries)

    def make_decision(self, check_result: CheckResult):
        """
        Make a decision based on given check_result

        :param check_result: `CheckResult` instance

        :return:
        """
        if check_result.is_failed:
            # Get non-critical errors first
            warnings = check_result.get_checks(**cfg.NON_CRITICALLY_FAILED)
            warning_msg = self.format_checks(*warnings)
            logger.warning(f"Some of the checks have failed: {warning_msg}."
                           "\nThe process can still continue. "
                           "It is best to ensure the issues are resolved.")

            # verify if some of critical errors failed
            if check_result.has_critical_failure:
                critical_checks = check_result.get_checks(
                                                    **cfg.CRITICALLY_FAILED)
                error_msg = self.format_checks(*critical_checks)
                logger.error(
                        f"FAILED: Critical checks - {error_msg}"
                        "\nCannot proceed further until they pass."
                )
                raise CriticalValidationError(error_msg)
        else:
            logger.info("All checks are passed")


class PreChecksDecisionMaker(DecisionMaker):

    """Class analyses `CheckResult` structure for all
       Pre-Checks - Deployment, and Replace Nodes
       and in case of errors, will stop the flow right there.
    """

    def make_decision(self, check_result: CheckResult):
        """
        Make a decision based on given check_result

        :param CheckResult check_result: instance with all checks needed for
                                         to make a decision
        :return:
        """
        failed = check_result.get_checks(failed=True)
        if failed:
            failed_msg = self.format_checks(*failed)
            raise ValidationError("One or more Pre-Flight "
                                  f"Checks have failed: {failed_msg}")

        logger.info("All Pre-Flight Checks have Passed")


class PostChecksDecisionMaker(DecisionMaker):

    """Class analyses `CheckResult` structure for all
       Post-Checks - Deployment, and Replace Nodes
       and in case of errors, will raise Warning to the User.
    """

    def make_decision(self, check_result: CheckResult):
        """
        Make a decision based on given check_result

        :param CheckResult check_result: instance with all checks needed for
                                         to make a decision
        :return:
        """
        if check_result.is_failed:
            failed = check_result.get_checks(failed=True)
            failed_msg = self.format_checks(*failed)
            logger.warning("One or more Post-routine Validations "
                           f"have failed: {failed_msg}")
        else:
            logger.info("Post-Routine Validations Completed")


class SWUpdateDecisionMaker(DecisionMaker):
    """Class analyses `CheckResult` structure and will decide to continue or
       to stop SW Update routine.
    """

    def make_decision(self, check_result: CheckResult):
        """
        Make a decision for SW Update based on `CheckResult` analysis

        :param CheckResult check_result: instance with all checks needed for
                                         to make a decision
        :return:
        """
        if check_result.is_failed:
            # Threat all errors as warnings
            warnings = check_result.get_checks(failed=True)
            warning_msg = self.format_checks(*warnings)
            logger.warning("Some SW Update pre-flight checks are failed: "
                           f"{warning_msg}")
        else:
            logger.info("All SW Update pre-flight checks are passed")


class SWUpgradeDecisionMaker(DecisionMaker):
    """Class analyses `CheckResult` structure and will decide to continue or
       to stop SW Upgrade routine.
    """

    def make_decision(self, check_result: CheckResult):
        """
        Make a decision for SW Upgrade based on `CheckResult` analysis

        :param CheckResult check_result: instance with all checks needed for
                                         to make a decision
        :return:
        """
        if check_result.is_failed:
            # Threat all errors as warnings
            errors = check_result.get_checks(failed=True)
            errors_msg = self.format_checks(*errors)
            logger.error("Some SW Update pre-flight checks are failed: "
                         f"{errors_msg}")
            raise SWUpgradeError(
                f"The following checks are failed: '{errors_msg}'")
        else:
            logger.info("All SW Upgrade pre-flight checks are passed")


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


@attr.s(auto_attribs=True)
class Check(CommandParserFillerMixin):
    """
    Base class for system and system components health and status validation
    """

    input_type: Type[inputs.NoParams] = inputs.NoParams
    _run_args_type = CheckArgs

    _PRV_METHOD_MOD = "_"  # private method modificator

    STONITH = "stonith"
    ACCESSIBLE = "accessible"

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
        node_network_path = KeyPath(f'cluster/{minion_id}/network/data')

        pillar_keys = (PillarKey(cluster_path / 'type'),
                       PillarKey(node_network_path / "public_ip"),
                       PillarKey(node_network_path / "private_ip"),
                       PillarKey(cluster_path / "cluster_ip"))

        # maybe we need to call it from the all targets and analyze the output
        # from each node
        pillar = PillarResolver(cfg.LOCAL_MINION).get(pillar_keys)

        pillar = pillar.get(local_minion_id())  # type: dict

        for key in pillar_keys:
            _res = CheckEntry(cfg.Checks.NETWORK.value)
            if not pillar[key] or pillar[key] is values.MISSED:
                _res.set_fail(checked_target=str(key.keypath),
                              comment="value is not specified")
            elif pillar[key] is None:
                _res.set_fail(checked_target=str(key.keypath),
                              comment="value is unset")
            else:
                _res.set_passed(checked_target=str(key.keypath))

            res.append(_res)

        return res

    @staticmethod
    def _communicability(
            *, args: str,
            targets: Optional[Union[list, tuple, set]] = None) -> CheckEntry:
        """
        Check if nodes can communicate using `salt test.ping`

        :param args: communicability check specific parameters and arguments
        :param Optional[Union[list, tuple, set]] targets:
               target nodes where network checks will be executed
        :return:
        """
        res: CheckEntry = CheckEntry(cfg.Checks.COMMUNICABILITY.value)

        # TODO: need to resolve cfg.ALL_MINIONS alias
        #  to the list of minions
        # TODO: create check and return list of nodes which are down
        if targets is None:
            targets = list(salt.pillar_get())
        if check_salt_minions_are_ready(targets=targets):
            res.set_passed(checked_target=local_minion_id())
        else:
            res.set_fail(checked_target=local_minion_id())

        return res

    @staticmethod
    def _connectivity(*, servers: Union[list, tuple, set] = PENDING_SERVERS,
                      args: str) -> List[CheckEntry]:
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

        res: List[CheckEntry] = list()

        for addr in servers:
            check_entry: CheckEntry = CheckEntry(cfg.Checks.CONNECTIVITY.value)
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
                check_entry.set_fail(checked_target=targets,
                                     comment=(f"{cfg.CheckVerdict.FAIL.value}:"
                                              f" {addr} is not reachable "
                                              f"from {targets}"))
            else:
                # if no error occurred
                check_entry.set_passed(checked_target=targets)

            res.append(check_entry)

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
                            'echo "\'{key_phrase}\' exists in logfile" && '
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
                    _res.set_fail(checked_target=minion_id,
                                  comment=f"{log_file}: {str(e.reason)}")
                    return _res

            _res.set_passed(checked_target=minion_id, comment=f"{log_file}")

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
                            args: str) -> List[CheckEntry]:
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

        res: List[CheckEntry] = list()

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

            check_ret: CheckEntry = CheckEntry(
                cfg.Checks.PASSWORDLESS_SSH_ACCESS.value)
            try:
                _ = cmd_run(cmd, targets=targets)
            except SaltCmdResultError:
                check_ret.set_fail(
                    checked_target=targets,
                    comment=(f"{cfg.CheckVerdict.FAIL.value}: "
                             f"'{addr}' is not reachable from "
                             f"{targets} under user {user}"))
            else:
                # if no error occurred
                check_ret.set_passed(checked_target=targets)

            res.append(check_ret)

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
        except Exception:
            res.set_fail(checked_target=local_minion_id())
        else:
            # if no error occurred
            res.set_passed(checked_target=local_minion_id())

        return res

    @staticmethod
    def _network_drivers(*, args: str) -> CheckEntry:
        """
        Check if Network Drivers are proper

        :param args: network_drivers check specific parameters and arguments
        :return:
        """
        res: CheckEntry = CheckEntry(cfg.Checks.NETWORK_DRIVERS.value)

        if cortx_py_utils_import_error:
            res.set_fail(checked_target=cfg.ALL_MINIONS,
                         comment="Package cortx-py-utils not installed")
            return res

        try:
            nodes = [
                node for node in Check._get_pillar_data("cluster").keys()
                if 'srvnode-' in node
            ]

            driver_args = [cfg.NETWORK_DRIVER] + nodes
            NetworkV().validate('drivers', driver_args)

        except Exception as exc:
            res.set_fail(checked_target=cfg.ALL_MINIONS,
                         comment=str(exc))
        else:
            res.set_passed(checked_target=cfg.ALL_MINIONS,
                           comment="Network Driver "
                           f"Validated: {driver_args}")

        return res

    @staticmethod
    def _network_hca(*, args: str) -> Union[CheckEntry, List[CheckEntry]]:
        """
        Check if Network HCA are proper

        :param args: network_hca check specific parameters and arguments
        :return:
        """
        check_value: CheckEntry = CheckEntry(cfg.Checks.NETWORK_HCA.value)

        if cortx_py_utils_import_error:
            check_value.set_fail(
                            checked_target=cfg.ALL_MINIONS,
                            comment="Package cortx-py-utils not installed")
            return check_value

        try:
            nodes = Check._get_nodes_list()
        except Exception as exc:
            check_value.set_fail(checked_target=cfg.ALL_MINIONS,
                                 comment=str(exc))
            return check_value

        res: List[CheckEntry] = list()

        for provider in cfg.HCA_PROVIDER:
            check_res: CheckEntry = CheckEntry(cfg.Checks.NETWORK_HCA.value)

            try:
                hca_args = [provider] + nodes
                NetworkV().validate('hca', hca_args)
            except Exception as exc:
                check_res.set_fail(checked_target=cfg.ALL_MINIONS,
                                   comment=str(exc))
            else:
                check_res.set_passed(checked_target=cfg.ALL_MINIONS,
                                     comment="HCA Presence and "
                                     f"Ports Validated: {hca_args}")

            res.append(check_res)

        return res

    @staticmethod
    def _storage_luns(*, args: str) -> Union[CheckEntry, List[CheckEntry]]:
        """
        Check if Storage LUNs are proper

        :param args: storage_luns check specific parameters and arguments
        :return:
        """
        check_value: CheckEntry = CheckEntry(cfg.Checks.STORAGE_LUNS.value)

        if cortx_py_utils_import_error:
            check_value.set_fail(
                            checked_target=cfg.ALL_MINIONS,
                            comment="Package cortx-py-utils not installed")
            return check_value

        try:
            nodes = Check._get_nodes_list()
        except Exception as exc:
            check_value.set_fail(checked_target=cfg.ALL_MINIONS,
                                 comment=str(exc))
            return check_value

        res: List[CheckEntry] = list()

        for luns_check in cfg.LUNS_CHECKS:
            check_res: CheckEntry = CheckEntry(cfg.Checks.STORAGE_LUNS.value)

            try:
                lun_args = [luns_check] + nodes
                StorageV().validate('luns', lun_args)
            except Exception as exc:
                check_res.set_fail(checked_target=cfg.ALL_MINIONS,
                                   comment=str(exc))
            else:
                check_res.set_passed(checked_target=cfg.ALL_MINIONS,
                                     comment="LUNs Accessibility, "
                                     "and Volume Size "
                                     f"Validated: {lun_args}")

            res.append(check_res)

        return res

    @staticmethod
    def _luns_mapped(*, args: str) -> CheckEntry:
        """
        Check if Storage LUNs are properly mapped

        :param args: luns_mapped check specific parameters and arguments
        :return:
        """
        res: CheckEntry = CheckEntry(cfg.Checks.LUNS_MAPPED.value)

        if cortx_py_utils_import_error:
            res.set_fail(checked_target=cfg.ALL_MINIONS,
                         comment="Package cortx-py-utils not installed")
            return res

        try:
            nodes = Check._get_nodes_list()

            lun_args = [cfg.LUNS_MAPPED_CHECK] + nodes
            StorageV().validate('luns', lun_args)

        except Exception as exc:
            res.set_fail(checked_target=cfg.ALL_MINIONS,
                         comment=str(exc))
        else:
            res.set_passed(checked_target=cfg.ALL_MINIONS,
                           comment="LUNs Mapped "
                           f"Validated: {lun_args}")

        return res

    @staticmethod
    def _storage_hba(*, args: str) -> Union[CheckEntry, List[CheckEntry]]:
        """
        Check if Storage HBA is proper

        :param args: storage_hba check specific parameters and arguments
        :return:
        """
        check_value: CheckEntry = CheckEntry(cfg.Checks.STORAGE_HBA.value)

        if cortx_py_utils_import_error:
            check_value.set_fail(
                                checked_target=cfg.ALL_MINIONS,
                                comment="Package cortx-py-utils not installed")
            return check_value

        try:
            nodes = Check._get_nodes_list()
        except Exception as exc:
            check_value.set_fail(checked_target=cfg.ALL_MINIONS,
                                 comment=str(exc))
            return check_value

        res: List[CheckEntry] = list()

        for provider in cfg.HBA_PROVIDER:
            check_res: CheckEntry = CheckEntry(cfg.Checks.STORAGE_HBA.value)

            try:
                hba_args = [provider] + nodes
                StorageV().validate('hba', hba_args)
            except Exception as exc:
                check_res.set_fail(checked_target=cfg.ALL_MINIONS,
                                   comment=str(exc))
            else:
                check_res.set_passed(checked_target=cfg.ALL_MINIONS,
                                     comment="HBA Presence and "
                                     f"Ports Validated: {hba_args}")

            res.append(check_res)

        return res

    @staticmethod
    def _storage_lvms(*, args: str) -> CheckEntry:
        """Storage lvms check."""
        res: CheckEntry = CheckEntry(cfg.Checks.STORAGE_LVMS.value)

        if cortx_py_utils_import_error:
            res.set_fail(checked_target=cfg.ALL_MINIONS,
                         comment="Package cortx-py-utils not installed")
            return res

        try:
            nodes = Check._get_nodes_list()
            StorageV().validate('lvms', nodes)
        except Exception as exc:
            res.set_fail(checked_target=cfg.ALL_MINIONS,
                         comment=str(exc))
        else:
            res.set_passed(checked_target=cfg.ALL_MINIONS)

        return res

    @staticmethod
    def _mgmt_vip(*, args: str) -> CheckEntry:
        """
        Check Network mgmt vip

        :param args: mgmt_vip check specific parameters and arguments
        :return:
        """
        res: CheckEntry = CheckEntry(cfg.Checks.MGMT_VIP.value)

        if cortx_py_utils_import_error:
            res.set_fail(checked_target=cfg.ALL_MINIONS,
                         comment="Package cortx-py-utils not installed")
            return res

        try:
            mgmt_vip = Check._get_pillar_data("cluster/mgmt_vip")
            NetworkV().validate('connectivity', [mgmt_vip])
        except Exception as exc:
            res.set_fail(checked_target=local_minion_id(),
                         comment=str(exc))
        else:
            res.set_passed(checked_target=local_minion_id())

        return res

    @staticmethod
    def _hostnames(*, args: str) -> Union[CheckEntry, List[CheckEntry]]:
        """
        Check hostnames

        :param args: hostnames check specific parameters and arguments
        :return:
        """
        check_entry: CheckEntry = CheckEntry(cfg.Checks.HOSTNAMES.value)

        if cortx_py_utils_import_error:
            check_entry.set_fail(
                checked_target=cfg.ALL_MINIONS,
                comment="Package cortx-py-utils not installed")
            return check_entry

        try:
            # Get node list
            nodes = Check._get_nodes_list()
        except Exception as exc:
            check_entry.set_fail(checked_target=cfg.ALL_MINIONS,
                                 comment=str(exc))
            return check_entry

        res: List[CheckEntry] = list()

        for node in nodes:
            check_ent: CheckEntry = CheckEntry(cfg.Checks.HOSTNAMES.value)
            try:
                hostname = Check._get_pillar_data(
                                f"cluster/{node}/hostname")
                NetworkV().validate('connectivity', [hostname])
            except Exception as exc:
                check_ent.set_fail(checked_target=local_minion_id(),
                                   comment=str(exc))
            else:
                check_ent.set_passed(checked_target=hostname)

            res.append(check_ent)

        return res

    @staticmethod
    def _public_data_ip(*, args: str) -> Union[CheckEntry, List[CheckEntry]]:
        """
        Check public data ip

        :param args: public_data_ip check specific parameters and arguments
        :return:
        """
        check_entry: CheckEntry = CheckEntry(cfg.Checks.PUB_DATA_IP.value)

        if cortx_py_utils_import_error:
            check_entry.set_fail(
                checked_target=cfg.ALL_MINIONS,
                comment="Package cortx-py-utils not installed")
            return check_entry

        try:
            # Get node list
            nodes = Check._get_nodes_list()
        except Exception as exc:
            check_entry.set_fail(checked_target=cfg.ALL_MINIONS,
                                 comment=str(exc))
            return check_entry

        res: List[CheckEntry] = list()
        _IP_DEV_IFACE_TMPL = (
            "ip addr show dev {ifc} | grep 'inet' | grep '{ifc}'")

        for node in nodes:
            check_ret: CheckEntry = CheckEntry(cfg.Checks.PUB_DATA_IP.value)

            try:
                # Get list data network interfaces
                interfaces = Check._get_pillar_data(
                    f"cluster/{node}/network/data/public_interfaces")

                ifc = [ifc for ifc in interfaces if 's0f0' in ifc]

                if ifc:
                    # Get IP address assigned to interfaces
                    cmd = _IP_DEV_IFACE_TMPL.format(ifc=ifc[0])
                    _ip = cmd_run(cmd, targets=node,
                                  fun_kwargs=dict(python_shell=True))

                    # Extract IP address
                    ip = _ip[node].split()[1].split('/')[0]

                    # Check for connectivity of received IP
                    NetworkV().validate('connectivity', [ip])
                    check_ret.set_passed(checked_target=node)
                else:
                    check_ret.set_fail(checked_target=node,
                                       comment=("Public data interface "
                                                "'s0f0' not found. interfaces "
                                                f"available: {interfaces}"))
            except Exception as exc:
                check_ret.set_fail(checked_target=node, comment=str(exc))

            res.append(check_ret)

        return res

    @staticmethod
    def _controller_ip(*, args: str) -> Union[CheckEntry, List[CheckEntry]]:
        """
        Check controller ips

        :param args: controller_ip check specific parameters and arguments
        :return:
        """
        check_entry: CheckEntry = CheckEntry(cfg.Checks.CONTROLLER_IP.value)

        if cortx_py_utils_import_error:
            check_entry.set_fail(
                checked_target=cfg.ALL_MINIONS,
                comment="Package cortx-py-utils not installed")
            return check_entry

        try:
            # Get node list
            nodes = Check._get_nodes_list()
        except Exception as exc:
            check_entry.set_fail(checked_target=cfg.ALL_MINIONS,
                                 comment=str(exc))
            return check_entry

        res: List[CheckEntry] = list()

        for node in nodes:
            check_ret: CheckEntry = CheckEntry(cfg.Checks.CONTROLLER_IP.value)

            try:
                # TODO: Update logic to dynamically identify
                # enclosure_id from node_id
                enclosure = "enclosure-1"
                primary_ip = Check._get_pillar_data(
                                f"storage/{enclosure}/controller/primary/ip"
                            )
                secondary_ip = Check._get_pillar_data(
                                f"storage/{enclosure}/controller/secondary/ip"
                            )

                # Check for connectivity of received IPs
                NetworkV().validate('connectivity',
                                    [primary_ip, secondary_ip])
            except Exception as exc:
                check_ret.set_fail(checked_target=node, comment=str(exc))
            else:
                check_ret.set_passed(checked_target=node)

            res.append(check_ret)

        return res

    def _bmc_accessibility(self, *, args: str) -> CheckEntry:
        """
        Check BMC accessibility

        :param args: bmc accessibility check specific parameters and arguments
        :return:
        """
        return self._validate_bmc_check(self.ACCESSIBLE)

    def _bmc_stonith(self, *, args: str) -> Union[CheckEntry,
                                                  List[CheckEntry]]:
        """
        Check BMC Stonith Configuration

        :param args: bmc stonith configuration check specific
                     parameters and arguments
        :return:
        """
        return self._validate_bmc_check(self.STONITH)

    def _validate_bmc_check(self, check: str):

        if check == self.STONITH:
            bmc_check = cfg.Checks.BMC_STONITH.value
        elif check == self.ACCESSIBLE:
            bmc_check = cfg.Checks.BMC_ACCESSIBILITY.value
        else:
            raise ValueError(f'BMC Check "{check}" is not supported')

        check_entry: CheckEntry = CheckEntry(bmc_check)
        # Check for import errors
        if cortx_py_utils_import_error:
            check_entry.set_fail(
                checked_target=cfg.ALL_MINIONS,
                comment="Package cortx-py-utils not installed")
            return check_entry

        try:
            # Get node list
            nodes = Check._get_nodes_list()
        except Exception as exc:
            check_entry.set_fail(checked_target=cfg.ALL_MINIONS,
                                 comment=str(exc))
            return check_entry

        res: List[CheckEntry] = list()
        #  TODO use of salt python API with function_run
        _DECRYPT_PSWD_CMD = ('salt-call lyveutils.decrypt cluster {val}'
                             ' --output=newline_values_only')
        minion_id = local_minion_id()

        for node in nodes:
            check_res: CheckEntry = CheckEntry(bmc_check)

            try:
                # Get BMC IP, user and secret.
                bmc_ip = Check._get_pillar_data(f"cluster/{node}/bmc/ip")
                bmc_user = Check._get_pillar_data(f"cluster/{node}/bmc/user")
                secret = Check._get_pillar_data(f"cluster/{node}/bmc/secret")

                # Decrypt the secret
                cmd = _DECRYPT_PSWD_CMD.format(val=secret)
                bmc_passwd = cmd_run(cmd, targets=minion_id)[minion_id]

                # Check the stonith configuration
                BmcV().validate(check, [node, bmc_ip, bmc_user, bmc_passwd])
            except Exception as exc:
                check_res.set_fail(checked_target=node, comment=str(exc))
            else:
                check_res.set_passed(checked_target=node)

            res.append(check_res)

        return res

    @staticmethod
    def _get_pillar_data(key):
        """Retrieve pillar data."""
        pillar_key = PillarKey(key)
        pillar = PillarResolver(cfg.LOCAL_MINION).get([pillar_key])
        pillar = next(iter(pillar.values()))

        if not pillar[pillar_key] or pillar[pillar_key] is values.MISSED:
            raise ValueError(f"value is not specified for {key}")
        else:
            return pillar[pillar_key]

    @staticmethod
    def _get_nodes_list():
        """Retrieve node  list from pillar"""
        nodes = []
        for key in Check._get_pillar_data("cluster"):
            if 'srvnode' in key:
                nodes.append(key)
        return nodes

    @staticmethod
    def _upgrade_iso_version(*, args: str) -> CheckEntry:
        """
        Validate upgrade ISO version validation

        Parameters
        ----------
        args: str
            Upgrade ISO version validation specific arguments and parameters

        Returns
        -------
        CheckEntry:
            CheckEntry instance with validation result

        """
        # TODO: dynamic import is needed here to solve cross imports issues
        #  between: `api/python/provisioner/commands/__init__.py` and
        #  `api/python/provisioner/commands/upgrade/set_swupgrade_repo.py`:
        #  SetSWUpgradeRepo imports Set class.
        from provisioner.commands.upgrade import GetISOVersion

        res: CheckEntry = CheckEntry(cfg.Checks.UPGRADE_ISO_VERSION.value)

        try:
            iso_version = GetISOVersion().run()
        except Exception as exc:
            res.set_fail(checked_target=local_minion_id(),
                         comment=str(exc))
        else:
            if iso_version is None:
                res.set_fail(checked_target=local_minion_id(),
                             comment='Current release version is equal to SW '
                                     'upgrade ISO version')
            else:
                res.set_passed(checked_target=local_minion_id())

        return res

    @staticmethod
    def _active_upgrade_iso(*, args: str) -> CheckEntry:
        """
        Ensure that no active upgrade ISO is available

        Parameters
        ----------
        args: str
            Active upgrade ISO validation specific arguments and parameters

        Returns
        -------
        CheckEntry:
            CheckEntry instance with validation result

        """
        # TODO: dynamic import is needed here to solve cross imports issues
        #  between: `api/python/provisioner/commands/__init__.py` and
        #  `api/python/provisioner/commands/upgrade/set_swupgrade_repo.py`:
        #  SetSWUpgradeRepo imports Set class.
        from provisioner.commands.upgrade import GetISOVersion

        res: CheckEntry = CheckEntry(cfg.Checks.ACTIVE_UPGRADE_ISO.value)

        try:
            iso_version = GetISOVersion().run()
        except Exception as exc:
            res.set_fail(checked_target=local_minion_id(),
                         comment=str(exc))
        else:
            if iso_version is None:
                # NOTE: GetISOVersion returns None in two cases:
                #  1. release version is equal to upgrade version, e.g. last
                #     upgrade ISO was applied
                #  2. there are no configured ISOs for the SW upgrade
                #  Both cases mean that there are no active upgrade ISO
                res.set_passed(checked_target=local_minion_id(),
                               comment='There are no active SW upgrade ISO'
                                       'detected')
            else:
                res.set_fail(checked_target=local_minion_id(),
                             comment="An active upgrade ISO is detected")

        return res

    @staticmethod
    def _packages_compatibility(args: str) -> CheckEntry:
        """
        Validate that SW upgrade packages are compatible with installed ones

        Parameters
        ----------
        args: str
            Specific parameters and arguments for package compatibility
            validation

        Returns
        -------
        CheckEntry:
            CheckEntry instance with validation result

        """
        from provisioner.commands.upgrade import GetSWUpgradeInfo

        res: CheckEntry = CheckEntry(cfg.Checks.PACKAGES_COMPATIBILITYO.value)

        iso_info = GetSWUpgradeInfo().run()  # check the latest SW upgrade

        try:
            CompatibilityValidator().validate(iso_info)
        except ValidationError as exc:
            res.set_fail(checked_target=local_minion_id(),
                         comment=str(exc))
        else:
            res.set_passed(checked_target=local_minion_id(),
                           comment='Packages compatibility check succeeded')

        return res

    def run(self, check_name: str = "",
            check_args: str = "") -> CheckResult:
        """
        Basic run method to execute checks specified by `check_name` or
        perform all checks if `check_name` is omitted

        :param str check_name: specific command to be executed on target nodes
        :param str check_args: check specific arguments

        :return:
        """
        res: CheckResult = CheckResult()

        # Check whether to execute all checks
        if check_name is None or check_name == cfg.GroupChecks.ALL.value:
            check_lists = cfg.CHECKS

        # Check whether to perform group check
        elif check_name in cfg.GROUP_CHECKS:
            check_lists = getattr(cfg, check_name.strip().upper())

        # Check for supported check name
        elif check_name.strip().lower() in cfg.CHECKS:
            check_lists = [check_name.strip().lower()]

        else:
            raise ValueError(f'Check "{check_name}" is not supported')

        for check_name in check_lists:
            _res = getattr(self,
                           self._PRV_METHOD_MOD + check_name)(args=check_args)
            res.add_checks(_res)  # aggregate all check results

        return res
