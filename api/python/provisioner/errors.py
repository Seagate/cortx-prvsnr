from typing import Dict, Union, Any

# TODO TEST for all


class ProvisionerError(Exception):
    pass


class ProvisionerCliError(ProvisionerError):
    pass


class BadPillarDataError(ProvisionerError):
    pass


class UnknownParamError(ProvisionerError):
    pass


# TODO TEST EOS-8473
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


class SaltError(ProvisionerError):
    pass


# TODO TEST
# TODO TYPING
class SaltCmdError(SaltError):
    _prvsnr_type_ = True

    def __init__(
        self, cmd_args: Any, reason: str = 'unknown'
    ):
        self.cmd_args = cmd_args
        self.reason = reason

    def __str__(self):
        return (
            "salt command failed, reason {}, args {}"
            .format(self.reason, self.cmd_args)
        )


# TODO TEST
class SaltCmdRunError(SaltCmdError):
    pass


class SaltCmdResultError(SaltCmdError):
    pass


# TODO TEST
class SaltNoReturnError(SaltCmdRunError):
    pass


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


class EOSUpdateRepoSourceError(ProvisionerError, ValueError):
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


# TODO IMPROVE DRY
class PillarSetError(ProvisionerError):
    _prvsnr_type_ = True

    def __init__(self, reason: Union[str, Exception], rollback_error=None):
        self.reason = reason
        self.rollback_error = rollback_error

    def __str__(self):
        return (
            'pillar update failed: {!r}'.format(self)
        )

    def __repr__(self):
        return (
            "{}(reason={!r}, rollback_error={!r})"
            .format(self.__class__.__name__, self.reason, self.rollback_error)
        )


# TODO TEST
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


# TODO TEST
class ClusterMaintenanceEnableError(ClusterMaintenanceError):
    def __init__(self, reason: Union[Exception, str]):
        super().__init__(True, reason)


# TODO TEST
class ClusterMaintenanceDisableError(ClusterMaintenanceError):
    def __init__(self, reason: Union[Exception, str]):
        super().__init__(False, reason)


# TODO TEST
class SWStackUpdateError(ProvisionerError):
    _prvsnr_type_ = True

    def __init__(self, reason: Union[Exception, str]):
        self.reason = reason

    def __str__(self):
        return (
            'failed to update SW stack, reason: {!r}'
            .format(self.reason)
        )


# TODO TEST EOS-8940
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


# TODO TEST
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


# TODO TEST
class SWUpdateFatalError(SWUpdateError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "FATAL: {}".format(super().__str__())
