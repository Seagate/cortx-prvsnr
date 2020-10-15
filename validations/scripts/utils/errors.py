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

from typing import Dict, Union, Any


class ProvisionerError(Exception):
    pass


class ProvisionerCliError(ProvisionerError):
    pass



class UnknownParamError(ProvisionerError):
    pass


class LogMsgTooLong(ProvisionerError):
    pass



class SubprocessCmdError(ProvisionerError):
    _prvsnr_type_ = True

    def __init__(
        self, cmd, cmd_args: Any, reason: str = 'unknown'
    ):
        self.cmd = cmd
        self.cmd_args = cmd_args
        self.reason = reason

    def __str__(self):
        return (
            "subprocess command failed, reason {}, args {}"
            .format(self.reason, self.cmd_args)
        )

class PrvsnrTypeDecodeError(ProvisionerError, ValueError):
    _prvsnr_type_ = True

    def __init__(self, spec: Dict, reason: Union[str, Exception]):
        self.spec = spec
        self.reason = reason

    def __str__(self):
        return (
            'decode failed for {}, reason: {!r}'
            .format(self.spec, self.reason)
        )


class SWUpdateRepoSourceError(ProvisionerError, ValueError):
    _prvsnr_type_ = True

    def __init__(self, source: str, reason: str):
        self.source = source
        self.reason = reason

    def __str__(self):
        return (
            'repo source {} is not acceptable, reason: {!r}'
            .format(self.source, self.reason)
        )


class PrvsnrCmdError(ProvisionerError):
    def __init__(self, cmd_id: str):
        self.cmd_id = cmd_id


class PrvsnrCmdNotFoundError(ProvisionerError):
    pass

class PrvsnrCmdNotFinishedError(ProvisionerError):
    pass


class ClusterMaintenanceError(ProvisionerError):
    _prvsnr_type_ = True

    def __init__(self, enable: bool, reason: Union[Exception, str]):
        self.enable = enable
        self.reason = reason

    def __str__(self):
        return (
            'failed to {} cluster maintenance, reason: {!r}'
            .format('enable' if self.enable else 'disable', self.reason)
        )


class ClusterMaintenanceEnableError(ClusterMaintenanceError):
    def __init__(self, reason: Union[Exception, str]):
        super().__init__(True, reason)


class ClusterMaintenanceDisableError(ClusterMaintenanceError):
    def __init__(self, reason: Union[Exception, str]):
        super().__init__(False, reason)

class SWStackUpdateError(ProvisionerError):
    _prvsnr_type_ = True

    def __init__(self, reason: Union[Exception, str]):
        self.reason = reason

    def __str__(self):
        return (
            'failed to update SW stack, reason: {!r}'
            .format(self.reason)
        )


class HAPostUpdateError(ProvisionerError):
    _prvsnr_type_ = True

    def __init__(self, reason: Union[Exception, str]):
        self.reason = reason

    def __str__(self):
        return (
            'failed to apply Hare post_update logic, reason: {!r}'
            .format(self.reason)
        )


class ClusterNotHealthyError(ProvisionerError):
    _prvsnr_type_ = True

    def __init__(self, reason: Union[Exception, str]):
        self.reason = reason

    def __str__(self):
        return (
            'failed to apply Hare post_update logic, reason: {!r}'
            .format(self.reason)
        )


class SWUpdateError(ProvisionerError):
    _prvsnr_type_ = True

    # FIXME reason might be an exception
    def __init__(self, reason: str, rollback_error=None):
        self.reason = reason
        self.rollback_error = rollback_error

    def __str__(self):
        return (
            'update failed: {!r}'.format(self)
        )

    def __repr__(self):
        return (
            "{}(reason={!r}, rollback_error={!r})"
            .format(self.__class__.__name__, self.reason, self.rollback_error)
        )

class SWUpdateFatalError(SWUpdateError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "FATAL: {}".format(super().__str__())


class SSLCertsUpdateError(ProvisionerError):
    _prvsnr_type_ = True

    def __init__(self, reason: ProvisionerError, rollback_error=None):
        self.reason = reason
        self.rollback_error = rollback_error

    def __str__(self):
        return (
            'SSL Cert update failed: {!r}'.format(self)
        )

    def __repr__(self):
        return (
            "{}(reason={!r}, rollback_error={!r})"
            .format(self.__class__.__name__, self.reason, self.rollback_error)
        )

