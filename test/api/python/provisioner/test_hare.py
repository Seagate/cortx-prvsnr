#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#
import pytest

from provisioner.config import LOCAL_MINION
from provisioner import hare

from .helper import mock_fun_result, mock_fun_echo


def test_cluster_stop(monkeypatch):
    def cb(*args, **kwargs):
        return {'res': (args, kwargs)}

    monkeypatch.setattr(hare, 'cmd_run', mock_fun_result(cb))

    res = hare.cluster_stop()

    assert res == (
        ('pcs cluster stop --all',),
        dict(targets=LOCAL_MINION)
    )


def test_cluster_start(monkeypatch):
    def cb(*args, **kwargs):
        return {'res': (args, kwargs)}

    monkeypatch.setattr(hare, 'cmd_run', mock_fun_result(cb))

    res = hare.cluster_start()

    assert res == (
        ('pcs cluster start --all',),
        dict(targets=LOCAL_MINION)
    )


def test_cluster_maintenance(monkeypatch):
    def cb(*args, **kwargs):
        return {'res': (args, kwargs)}

    monkeypatch.setattr(hare, 'cmd_run', mock_fun_result(cb))

    res = hare.cluster_maintenance(True)
    assert res == (
        ('hctl node maintenance --all --timeout-sec=600',),
        dict(targets=LOCAL_MINION, background=False, timeout=660)
    )

    res = hare.cluster_maintenance(True, verbose=False)
    assert res == (
        ('hctl node maintenance --all --timeout-sec=600',),
        dict(targets=LOCAL_MINION, background=False, timeout=660)
    )

    res = hare.cluster_maintenance(True, timeout=123)
    assert res == (
        ('hctl node maintenance --all --timeout-sec=123',),
        dict(targets=LOCAL_MINION, background=False, timeout=183)
    )

    res = hare.cluster_maintenance(True, background=True)
    assert res == (
        ('hctl node maintenance --all --timeout-sec=600',),
        dict(targets=LOCAL_MINION, background=True, timeout=660)
    )

    res = hare.cluster_maintenance(False)
    assert res == (
        ('hctl node unmaintenance --all --timeout-sec=600',),
        dict(targets=LOCAL_MINION, background=False, timeout=660)
    )


def test_cluster_maintenance_enable(monkeypatch):
    monkeypatch.setattr(hare, 'cluster_maintenance', mock_fun_echo())
    res = hare.cluster_maintenance_enable(
        timeout=1, verbose=True, background=True
    )
    assert res == (
        (True,),
        dict(timeout=1, verbose=True, background=True)
    )


def test_cluster_maintenance_disable(monkeypatch):
    monkeypatch.setattr(hare, 'cluster_maintenance', mock_fun_echo())
    res = hare.cluster_maintenance_disable(
        timeout=321, verbose=False, background=True
    )
    assert res == (
        (False,),
        dict(timeout=321, verbose=False, background=True)
    )


def test_check_cluster(mocker):
    some_path = 'some/path'
    cmd_run_m = mocker.patch.object(hare, 'cmd_run', autospec=True)

    path_m = mocker.patch.object(hare, 'PRVSNR_ROOT_DIR', autospec=True)
    path_m.__truediv__().__str__.return_value = some_path
    path_m.__truediv__().exists.return_value = False

    with pytest.raises(RuntimeError) as excinfo:
        hare.check_cluster_is_online()

    assert str(excinfo.value) == 'Utility scripts are not found'

    path_m.__truediv__().exists.return_value = True
    cmd_run_m.return_value = {1: 2, 3: 4}
    assert hare.check_cluster_is_online() == 2

    cmd_run_m.assert_called_once_with(
        f"bash -c '. {some_path}; ensure_healthy_cluster false'",
        targets=LOCAL_MINION
    )


def test_ensure_cluster_is_stopped(monkeypatch):

    stopped = True

    def cluster_stop():
        nonlocal stopped
        stopped = True

    monkeypatch.setattr(hare, 'cluster_stop', mock_fun_result(cluster_stop))
    hare.ensure_cluster_is_stopped()

    assert stopped


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

    monkeypatch.setattr(hare, 'cluster_start', mock_fun_result(cluster_start))
    monkeypatch.setattr(hare, 'ensure', mock_fun_result(ensure))
    hare.ensure_cluster_is_started()

    assert started
    assert _cb is hare.check_cluster_is_online
    assert _tries == 30
    assert _wait == 10
