import pytest

from provisioner import _api as api
from provisioner.errors import UnknownParamError


def test_api_get_params_fails_for_unknown_param(monkeypatch):
    monkeypatch.setattr(api, 'api_spec', {})
    with pytest.raises(UnknownParamError):
        api.get_params('some-param')
