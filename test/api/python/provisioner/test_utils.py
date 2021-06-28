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
import subprocess
import yaml

from provisioner import config
from provisioner import errors
from provisioner import utils


@pytest.fixture
def dump_yaml_defaults():
    return {
        'canonical': False,
        'default_flow_style': False,
        'indent': 4,
        'width': 1,
    }


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


def test_run_subprocess_cmd_prepares_str(mocker):
    cmd_name = "ls -la aaa bbb"
    kwargs = dict(
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    kwargs.update(kwargs)
    kwargs["check"] = True

    run_m = mocker.patch.object(utils.subprocess, 'run', autospec=True)

    utils.run_subprocess_cmd(cmd_name)
    run_m.assert_called_once_with(cmd_name.split(), **kwargs)


@pytest.mark.patch_logging([(utils, ('error',))])
def test_run_subprocess_cmd_raises_exception(mocker, patch_logging):
    cmd_name = "some command"

    mocker.patch.object(
        utils.subprocess, 'run', autospec=True, side_effect=FileNotFoundError
    )
    with pytest.raises(errors.SubprocessCmdError) as exec:
        utils.run_subprocess_cmd(cmd_name)

    assert "FileNotFoundError" in str(exec.value.reason)


@pytest.mark.outdated
def test_run_subprocess_cmd_happy_path(mocker):
    cmd_name = "ls -l"
    return_value = "some-return-value"

    mocker.patch.object(
        utils.subprocess, 'run', autospec=True, return_value=return_value
    )

    assert utils.run_subprocess_cmd(cmd_name) == return_value


def test_run_subprocess_cmd_check_is_kept(mocker):
    cmd_name = "ls"
    kwargs = dict(
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    run_m = mocker.patch.object(utils.subprocess, 'run', autospec=True)

    kwargs["check"] = False
    utils.run_subprocess_cmd(cmd_name, **kwargs)
    run_m.assert_called_with([cmd_name], **kwargs)

    kwargs["check"] = True
    utils.run_subprocess_cmd(cmd_name, **kwargs)
    run_m.assert_called_with([cmd_name], **kwargs)


def test_repo_tgz_with_invalid_path(mocker, tmpdir_function):
    project_path = ""
    dest_dir = tmpdir_function / 'some_path'

    mocker.patch.object(utils, 'run_subprocess_cmd', autospec=True)

    with pytest.raises(ValueError) as exec:
        utils.repo_tgz(dest_dir, project_path)

    assert "project path is not specified" in str(exec.value)


def test_repo_tgz_happy_path_no_ver(mocker, tmpdir_function):
    dest_dir = tmpdir_function / 'repo_tgz_path'
    project_path = 'some-path'
    include_dirs = ['dir1', 'dir2']

    class somecls:
        pass

    mock_ret = somecls()
    mock_ret.stdout = 'tar (GNU tar) 1.30'

    run_m = mocker.patch.object(
        utils, 'run_subprocess_cmd', autospec=True, return_value=mock_ret
    )

    assert utils.repo_tgz(
        dest_dir, project_path=project_path, include_dirs=include_dirs
    ) == dest_dir

    run_m.assert_called_with(
        ['tar', '-czf', str(dest_dir)]
        + [
            '--exclude-vcs',
            '--exclude-from', str(config.PROJECT_PATH / '.gitignore'),
            '--sort', 'name'
        ]
        + ['-C', project_path]
        + include_dirs
    )


def test_repo_tgz_happy_path_with_ver(mocker, tmpdir_function):
    dest_dir = tmpdir_function / 'repo_tgz_path'
    project_path = 'some-project-path'
    version = '1.0'
    include_dirs = ['dir1', 'dir2']

    run_m = mocker.patch.object(utils, 'run_subprocess_cmd', autospec=True)

    assert utils.repo_tgz(
        dest_dir, project_path=project_path,
        version=version, include_dirs=include_dirs
    ) == dest_dir
    run_m.assert_called_once_with(
        ['git', 'archive', '--format=tar.gz', version, '-o', str(dest_dir)]
        + include_dirs
    )


@pytest.mark.patch_logging([(utils, ('error',))])
def test_load_yaml_str_raises_exception(mocker, patch_logging):
    data = 'some-data'

    mocker.patch.object(
        utils.yaml, 'safe_load',
        autospec=True, side_effect=yaml.YAMLError
    )

    with pytest.raises(yaml.YAMLError):
        utils.load_yaml_str(data)


def test_load_yaml_str_input_check(mocker):
    data = 'some-data'

    run_m = mocker.patch.object(utils.yaml, 'safe_load', autospec=True)
    utils.load_yaml_str(data)

    run_m.assert_called_once_with(data)


def test_load_yaml_str_output_check(mocker):
    in_data = 'some-in-data'
    out_data = 'some-out-data'

    mocker.patch.object(
        utils.yaml, 'safe_load', autospec=True, return_value=out_data
    )

    assert utils.load_yaml_str(in_data) == out_data


def test_dump_yaml_str_input_check(mocker, dump_yaml_defaults):
    data = 'some-data'

    run_m = mocker.patch.object(utils.yaml, 'dump', autospec=True)

    utils.dump_yaml_str(data)

    run_m.assert_called_once_with(data, **dump_yaml_defaults)


def test_dump_yaml_str_output_check(mocker):
    in_data = 'some-in-data'
    out_data = 'some-out-data'

    mocker.patch.object(
        utils.yaml, 'dump', autospec=True, return_value=out_data
    )

    assert utils.dump_yaml_str(in_data) == out_data


def test_load_yaml_input_check(mocker):
    data_file = 'some-file'
    data_file_content = 'some-file-content'

    path_m = mocker.patch.object(utils, 'Path', autospec=True)
    path_m().read_text.return_value = data_file_content
    run_m = mocker.patch.object(utils, 'load_yaml_str', autospec=True)

    utils.load_yaml(data_file)
    run_m.assert_called_once_with(data_file_content)


def test_load_yaml_output_check(mocker):
    out_data = 'some-out-data'
    data_file = 'some-file'
    data_file_content = 'some-file-content'

    path_m = mocker.patch.object(utils, 'Path', autospec=True)
    path_m().read_text.return_value = data_file_content

    mocker.patch.object(
        utils, 'load_yaml_str', autospec=True, return_value=out_data
    )

    assert utils.load_yaml(data_file) == out_data


@pytest.mark.patch_logging([(utils, ('error',))])
def test_load_yaml_raises_exception(mocker, patch_logging):
    data_file = 'some-file'
    data_file_content = 'some-file-content'

    path_m = mocker.patch.object(utils, 'Path', autospec=True)
    path_m().read_text.return_value = data_file_content

    mocker.patch.object(
        utils, 'load_yaml_str', autospec=True, side_effect=yaml.YAMLError
    )

    with pytest.raises(yaml.YAMLError):
        utils.load_yaml(data_file)


def test_dump_yaml_input_check(mocker):
    data_file = 'some-file'
    data_file_content = 'some-file-content'

    mocker.patch.object(utils, 'Path', autospec=True)

    run_m = mocker.patch.object(utils, 'dump_yaml_str', autospec=True)

    utils.dump_yaml(data_file, data_file_content)
    run_m.assert_called_once_with(data_file_content)
