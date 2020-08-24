from provisioner.errors import (
    ProvisionerError, SubprocessCmdError, SaltCmdError,
    PrvsnrTypeDecodeError, SWUpdateRepoSourceError, PillarSetError,
    ClusterMaintenanceError, ClusterMaintenanceEnableError,
    ClusterMaintenanceDisableError, SWStackUpdateError, HAPostUpdateError,
    ClusterNotHealthyError, SWUpdateError, SWUpdateFatalError,
    SSLCertsUpdateError, ReleaseFileNotFoundError
)


def test_subprocess_cmd_error_str():
    cmd = 'some-command'
    cmd_args = 'some-args'
    reason = 'some-reason'

    obj = SubprocessCmdError(cmd, cmd_args, reason)

    assert str(obj) == f"subprocess command failed, reason {reason}, args " \
        f"{cmd_args}"


def test_salt_cmd_error_str():
    cmd_args = 'some-args'
    reason = 'some-reason'

    obj = SaltCmdError(cmd_args, reason)

    assert str(obj) == f"salt command failed, reason {reason}, args " \
        f"{cmd_args}"


def test_prvsnr_type_decode_error_str():
    spec_dict = {'1': {'2': '3'}}
    reason = 'some-reason'

    obj = PrvsnrTypeDecodeError(spec_dict, reason)

    assert str(obj) == "decode failed for {}, reason: {!r}".format(spec_dict,
                                                                   reason)


def test_sw_update_repo_source_error_str():
    source = 'some-src'
    reason = 'some-reason'

    obj = SWUpdateRepoSourceError(source, reason)

    assert str(obj) == 'repo source {} is not acceptable, reason: {!r}'.format(
        source, reason)


def test_pillar_set_error_str():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = PillarSetError(reason, rollback_error)

    assert str(obj) == "pillar update failed: {!r}".format(obj)


def test_pillar_set_error_repr():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = PillarSetError(reason, rollback_error)

    assert repr(obj) == "{}(reason={!r}, rollback_error={!r})".format(
        obj.__class__.__name__, reason, rollback_error)


def test_cluster_maintenance_error_str():
    enable = True
    reason = 'some-reason'

    obj = ClusterMaintenanceError(enable, reason)

    assert str(obj) == "failed to {} cluster maintenance, reason: {!r}".format(
        'enable', reason)


def test_cluster_maintenance_enable_error_init():
    reason = 'some-reason'

    obj = ClusterMaintenanceEnableError(reason)
    assert obj.enable
    assert obj.reason == reason


def test_cluster_maintenance_disable_error_init():
    reason = 'some-reason'

    obj = ClusterMaintenanceDisableError(reason)
    assert not obj.enable
    assert obj.reason == reason


def test_sw_stack_update_error_str():
    reason = 'some-reason'

    obj = SWStackUpdateError(reason)

    assert str(obj) == "failed to update SW stack, reason: {!r}".format(reason)


def test_ha_post_update_error_str():
    reason = 'some-reason'

    obj = HAPostUpdateError(reason)

    assert str(obj) == "failed to apply Hare post_update logic, reason: {!r}"\
        .format(reason)


def test_cluster_not_healthy_error_str():
    reason = 'some-reason'

    obj = ClusterNotHealthyError(reason)

    assert str(obj) == "failed to apply Hare post_update logic, reason: {!r}"\
        .format(reason)


def test_sw_update_error_str():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = SWUpdateError(reason, rollback_error)

    assert str(obj) == "update failed: {!r}".format(obj)


def test_sw_update_error_repr():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = SWUpdateError(reason, rollback_error)

    assert repr(obj) == "{}(reason={!r}, rollback_error={!r})".format(
        obj.__class__.__name__, reason, rollback_error)


def test_sw_update_fatal_error_str():
    reason = 'some-reason'
    rollback_error = 'some-error'

    obj = SWUpdateFatalError(reason, rollback_error)

    assert str(obj) == "FATAL: update failed: {!r}".format(obj)


def test_ssl_certs_update_error_str():
    prov_obj = ProvisionerError()
    rollback_error = 'some-error'

    obj = SSLCertsUpdateError(prov_obj, rollback_error)

    assert str(obj) == "SSL Cert update failed: {!r}".format(obj)


def test_ssl_certs_update_error_repr():
    reason = ProvisionerError()
    rollback_error = 'some-error'

    obj = SSLCertsUpdateError(reason, rollback_error)

    assert repr(obj) == "{}(reason={!r}, rollback_error={!r})".format(
        obj.__class__.__name__, reason, rollback_error)


def test_release_file_not_found_error_str():
    reason = 'some-reason'

    obj = ReleaseFileNotFoundError(reason)

    assert str(obj) == "RELEASE.INFO or RELEASE_FACTORY.INFO file is not " \
                       "found"


def test_release_file_not_found_error_repr():
    reason = 'some-reason'

    obj = ReleaseFileNotFoundError(reason)

    assert repr(obj) == "{}(reason={!r})".format(obj.__class__.__name__,
                                                 reason)
