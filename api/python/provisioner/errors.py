class ProvisionerError(Exception):
    pass


class BadPillarDataError(ProvisionerError):
    pass


class UnknownParamError(ProvisionerError):
    pass


class SaltError(ProvisionerError):
    pass
