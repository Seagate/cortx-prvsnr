#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import pytest

from provisioner.errors import (
    ProvisionerError, SubprocessCmdError, SaltCmdError,
    PrvsnrTypeDecodeError, SWUpdateRepoSourceError, PillarSetError,
    ClusterMaintenanceError, ClusterMaintenanceEnableError,
    ClusterMaintenanceDisableError, SWStackUpdateError, HAPostUpdateError,
    ClusterNotHealthyError, SWUpdateError, SWUpdateFatalError,
    SSLCertsUpdateError, ReleaseFileNotFoundError
)


def test_SubprocessCmdError_str():
    cmd = 'some-command'
    cmd_args = 'some-args'
    reason = 'some-reason'

    obj = SubprocessCmdError(cmd, cmd_args, reason)

    assert str(obj) == (
        f"subprocess command failed, reason '{reason}', args {cmd_args}"
    )


def test_SaltCmdError_str():
    cmd_args = 'some-args'
    reason = 'some-reason'

    obj = SaltCmdError(cmd_args, reason)

    assert str(obj) == (
        f"salt command failed, reason {reason}, args {cmd_args}")


@pytest.mark.outdated
def test_PrvsnrTypeDecodeError_str():
    spec_dict = {'1': {'2': '3'}}
    reason = 'some-reason'

    obj = PrvsnrTypeDecodeError(spec_dict, reason)

    assert str(obj) == "decode failed for {}, reason: {!r}".format(spec_dict,
                                                                   reason)


@pytest.mark.outdated
def test_SWUpdateRepoSourceError_str():
    source = 'some-src'
    reason = 'some-reason'

    obj = SWUpdateRepoSourceError(source, reason)

    assert str(obj) == 'repo source {} is not acceptable, reason: {!r}'.format(
        source, reason)


@pytest.mark.outdated
def test_PillarSetError_str():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = PillarSetError(reason, rollback_error)

    assert str(obj) == "pillar update failed: {!r}".format(obj)


def test_PillarSetError_repr():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = PillarSetError(reason, rollback_error)

    assert repr(obj) == "{}(reason={!r}, rollback_error={!r})".format(
        obj.__class__.__name__, reason, rollback_error)


@pytest.mark.outdated
def test_ClusterMaintenanceError_str():
    enable = True
    reason = 'some-reason'

    obj = ClusterMaintenanceError(enable, reason)

    assert str(obj) == "failed to {} cluster maintenance, reason: {!r}".format(
        'enable', reason)


def test_ClusterMaintenanceEnableError_init():
    reason = 'some-reason'

    obj = ClusterMaintenanceEnableError(reason)
    assert obj.enable
    assert obj.reason == reason


def test_ClusterMaintenanceDisableError_init():
    reason = 'some-reason'

    obj = ClusterMaintenanceDisableError(reason)
    assert not obj.enable
    assert obj.reason == reason


@pytest.mark.outdated
def test_SWStackUpdateError_str():
    reason = 'some-reason'

    obj = SWStackUpdateError(reason)

    assert str(obj) == "failed to update SW stack, reason: {!r}".format(reason)


@pytest.mark.outdated
def test_HAPostUpdateError_str():
    reason = 'some-reason'

    obj = HAPostUpdateError(reason)

    assert str(obj) == "failed to apply Hare post_update logic, reason: {!r}"\
        .format(reason)


@pytest.mark.outdated
def test_ClusterNotHealthyError_str():
    reason = 'some-reason'

    obj = ClusterNotHealthyError(reason)

    assert str(obj) == "failed to apply Hare post_update logic, reason: {!r}"\
        .format(reason)


@pytest.mark.outdated
def test_SWUpdateError_str():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = SWUpdateError(reason, rollback_error)

    assert str(obj) == "update failed: {!r}".format(obj)


def test_SWUpdateError_repr():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = SWUpdateError(reason, rollback_error)

    assert repr(obj) == "{}(reason={!r}, rollback_error={!r})".format(
        obj.__class__.__name__, reason, rollback_error)


@pytest.mark.outdated
def test_SWUpdateFatalError_str():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = SWUpdateFatalError(reason, rollback_error)

    assert str(obj) == "FATAL: update failed: {!r}".format(obj)


@pytest.mark.outdated
def test_SSLCertsUpdateError_str():
    prov_obj = ProvisionerError()
    rollback_error = 'some-error'

    obj = SSLCertsUpdateError(prov_obj, rollback_error)

    assert str(obj) == "SSL Cert update failed: {!r}".format(obj)


def test_SSLCertsUpdateError_repr():
    reason = ProvisionerError()
    rollback_error = 'some-error'

    obj = SSLCertsUpdateError(reason, rollback_error)

    assert repr(obj) == "{}(reason={!r}, rollback_error={!r})".format(
        obj.__class__.__name__, reason, rollback_error)


def test_ReleaseFileNotFoundError_str():
    reason = 'some-reason'

    obj = ReleaseFileNotFoundError(reason)

    assert str(obj) == "RELEASE.INFO or RELEASE_FACTORY.INFO file is not " \
                       "found"


def test_ReleaseFileNotFoundError_repr():
    reason = 'some-reason'

    obj = ReleaseFileNotFoundError(reason)

    assert repr(obj) == "{}(reason={!r})".format(obj.__class__.__name__,
                                                 reason)
