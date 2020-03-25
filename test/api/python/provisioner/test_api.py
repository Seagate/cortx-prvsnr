import pytest

from provisioner import _api as api
from provisioner.errors import UnknownParamError
from provisioner import inputs


@pytest.mark.patch_logging([(inputs, ('error',))])
def test_api_get_params_fails_for_unknown_param(
    monkeypatch, patch_logging
):
    monkeypatch.setattr(api, 'api_spec', {})
    with pytest.raises(UnknownParamError):
        api.get_params('some-param')
