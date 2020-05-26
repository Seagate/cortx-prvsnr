import pytest

from provisioner import errors
from provisioner import utils


# TODO IMPROVE split
@pytest.mark.patch_logging([(utils, ('debug', 'info'))])
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

    def check_cb():
        nonlocal ntries
        ntries += 1
        raise TypeError('some error')

    wait = 0
    ntries = 0
    with pytest.raises(TypeError):
        utils.ensure(check_cb, tries=21, wait=3)

    assert ntries == 1
    assert wait == 0

    wait = 0
    ntries = 0
    with pytest.raises(TypeError):
        utils.ensure(
            check_cb, tries=21, wait=3, expected_exc=TypeError
        )

    assert ntries == 21
    assert wait == 3

    wait = 0
    ntries = 0
    with pytest.raises(TypeError):
        utils.ensure(
            check_cb, tries=21, wait=3, expected_exc=(TypeError, ValueError)
        )

    assert ntries == 21
    assert wait == 3
