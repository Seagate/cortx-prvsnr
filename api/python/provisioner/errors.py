from typing import Dict, Union

# TODO tests for all


class ProvisionerError(Exception):
    pass


class BadPillarDataError(ProvisionerError):
    pass


class UnknownParamError(ProvisionerError):
    pass


class SaltError(ProvisionerError):
    pass


class SaltEmptyReturnError(SaltError):
    pass


class PrvsnrTypeDecodeError(ProvisionerError, ValueError):
    def __init__(self, spec: Dict, reason: Union[str, Exception]):
        self.spec = spec
        self.reason = reason

    def __str__(self):
        return (
            'decode failed for {}, reason: {!r}'
            .format(self.spec, self.reason)
        )


class EOSUpdateRepoSourceError(ProvisionerError, ValueError):
    def __init__(self, source: str, reason: str):
        self.source = source
        self.reason = reason

    def __str__(self):
        return (
            'repo source {} is not acceptable, reason: {}'
            .format(self.source, self.reason)
        )
