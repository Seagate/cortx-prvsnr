
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


class EOSUpdateRepoSourceError(ProvisionerError, ValueError):
    def __init__(self, source: str, reason: str):
        self.source = source
        self.reason = reason

    def __str__(self):
        return (
            'repo source {} is not acceptable, reason: {}'
            .format(self.source, self.reason)
        )
