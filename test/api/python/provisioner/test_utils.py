import pytest

from provisioner import errors
from provisioner import utils


@pytest.mark.patch_logging([(utils, ('debug',))])
def test_ensure(monkeypatch, patch_logging):

    wait = 0
    ntries = 0

    def sleep(_wait):
        nonlocal wait
        wait = _wait

    def check_cb():
        nonlocal ntries
        ntries += 1

    monkeypatch.setattr(utils.time, 'sleep', sleep)

    with pytest.raises(errors.ProvisionerError):
        utils.ensure(check_cb, tries=21, wait=3)

    assert ntries == 21
    assert wait == 3
