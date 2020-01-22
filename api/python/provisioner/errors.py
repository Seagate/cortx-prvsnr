class ProvisionerBaseException(Exception):
    pass


class BadPillarDataError(ProvisionerBaseException):
    pass


class UnknownParamError(ProvisionerBaseException):
    pass


class SaltError(ProvisionerBaseException):
    pass
