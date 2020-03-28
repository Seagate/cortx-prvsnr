from functools import partial
from typing import Callable

from provisioner.config import LOCAL_MINION
from provisioner import hare


def fun_mock(res, *args, **kwargs):
    if res:
        if isinstance(res, Callable):
            return res(*args, **kwargs)
        else:
            return res
    else:
        return (args, kwargs)


def fun_mock_echo():
    return partial(fun_mock, None)


def fun_mock_result(res):
    return partial(fun_mock, res)


def test_cluster_stop(monkeypatch):
    def cb(*args, **kwargs):
        return {'res': (args, kwargs)}

    monkeypatch.setattr(hare, 'cmd_run', fun_mock_result(cb))

    res = hare.cluster_stop()

    assert res == (
        ('pcs cluster stop --all',),
        dict(targets=LOCAL_MINION)
    )


def test_cluster_start(monkeypatch):
    def cb(*args, **kwargs):
        return {'res': (args, kwargs)}

    monkeypatch.setattr(hare, 'cmd_run', fun_mock_result(cb))

    res = hare.cluster_start()

    assert res == (
        ('pcs cluster start --all',),
        dict(targets=LOCAL_MINION)
    )


def test_cluster_status(monkeypatch, test_output_dir):
    test_output = (test_output_dir / 'pcs.status.offline.out').read_text()
    monkeypatch.setattr(hare, 'cluster_status', fun_mock_result(test_output))
    assert hare.check_cluster_is_offline()
    assert not hare.check_cluster_is_online()

    test_output = (test_output_dir / 'pcs.status.online.out').read_text()
    monkeypatch.setattr(hare, 'cluster_status', fun_mock_result(test_output))
    assert not hare.check_cluster_is_offline()
    assert hare.check_cluster_is_online()


def test_ensure_cluster_is_stopped(monkeypatch):

    stopped = True
    _tries = None
    _wait = None
    _cb = None

    def cluster_stop():
        nonlocal stopped
        stopped = True

    def ensure(cb, tries=None, wait=None):
        nonlocal _cb, _tries, _wait
        _cb = cb
        _tries = tries
        _wait = wait

    monkeypatch.setattr(hare, 'cluster_stop', fun_mock_result(cluster_stop))
    monkeypatch.setattr(hare, 'ensure', fun_mock_result(ensure))
    hare.ensure_cluster_is_stopped()

    assert stopped
    assert _cb is hare.check_cluster_is_offline
    assert _tries == 30
    assert _wait == 1


def test_ensure_cluster_is_started(monkeypatch):

    started = True
    _tries = None
    _wait = None
    _cb = None

    def cluster_start():
        nonlocal started
        started = True

    def ensure(cb, tries=None, wait=None):
        nonlocal _cb, _tries, _wait
        _cb = cb
        _tries = tries
        _wait = wait

    monkeypatch.setattr(hare, 'cluster_start', fun_mock_result(cluster_start))
    monkeypatch.setattr(hare, 'ensure', fun_mock_result(ensure))
    hare.ensure_cluster_is_started()

    assert started
    assert _cb is hare.check_cluster_is_online
    assert _tries == 30
    assert _wait == 10
