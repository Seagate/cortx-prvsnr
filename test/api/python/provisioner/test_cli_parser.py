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
from copy import deepcopy

from provisioner.vendor import attr
from provisioner.cli_parser import parse_args, ParseRes
from provisioner import errors, config
from provisioner.base import prvsnr_config
import builtins


# TODO tests for commands and args


# HELPERS AND FIXTURES


# --version provides a way for separate check for
# some args not allowed as standalone ones
def _parse_args(*args, add_version=True):
    if add_version:
        args = ['--version'] + list(args)
    return parse_args(args)


def check(expected, *args):
    expected.kwargs['version'] = True
    assert attr.astuple(
        _parse_args(*args, add_version=True)
    ) == attr.astuple(expected)


@pytest.fixture(scope='module')
def default_res():
    res = _parse_args('--version', add_version=False)
    res.kwargs['version'] = False
    return res


@pytest.fixture(scope='function')
def default_res_copy(default_res):
    return ParseRes(
        *deepcopy(attr.astuple(default_res))
    )


# @pytest.fixture
# def mock_print(mocker):
#     return mocker.patch('builtins.print', autospec=True)


# TESTS

@pytest.mark.skip(reason="EOS-18738")
def test_cli_parser_version(default_res_copy):
    default_res_copy.kwargs['version'] = True
    assert _parse_args(
        '--version', add_version=False
    ) == default_res_copy


@pytest.mark.skip(reason="EOS-18738")
def test_cli_parser_creds(default_res_copy):
    username = 'someuser'
    password = 'somepass'
    default_res_copy.kwargs['username'] = username
    default_res_copy.kwargs['password'] = password
    check(
        default_res_copy,
        '--username', username, '--password', password
    )


@pytest.mark.skip(reason="EOS-18738")
def test_cli_parser_eauth(default_res_copy):
    for eauth in ('pam', 'ldap'):
        default_res_copy.kwargs['eauth'] = eauth
        check(
            default_res_copy, '--eauth', eauth
        )

    # TODO patch print_usage
    # incorrect eauth
    eauth = 'someeauth'
    with pytest.raises(errors.ProvisionerCliError):
        _parse_args(
            '--eauth', eauth, add_version=True
        )


@pytest.mark.skip(reason="EOS-18738")
def test_cli_parser_output(default_res_copy):
    for output in config.PRVSNR_CLI_OUTPUT:
        default_res_copy.kwargs['output'] = output
        check(
            default_res_copy, '--output', output
        )

    # TODO patch print_usage
    # incorrect output
    output = 'someoutput'
    with pytest.raises(errors.ProvisionerCliError):
        _parse_args(
            '--output', output, add_version=True
        )


@pytest.mark.skip(reason="EOS-18738")
def test_cli_parser_logging_nohandler(default_res_copy, log_handler_name):
    default_res_copy.kwargs[f'{log_handler_name}'] = False
    check(
        default_res_copy,
        f'--no{log_handler_name}'
    )

    default_res_copy.kwargs[f'{log_handler_name}'] = True
    check(
        default_res_copy,
        f'--{log_handler_name}'
    )

    # TODO patch print_usage
    # incorrect handler
    with pytest.raises(errors.ProvisionerCliError):
        _parse_args(
            '--nosomehandler', add_version=True
        )


@pytest.mark.skip(reason="EOS-18738")
def test_cli_parser_logging_level(default_res_copy, log_handler_name):
    for level in ('DEBUG', 'INFO', 'WARN', 'ERROR'):
        default_res_copy.kwargs[f'{log_handler_name}_level'] = level
        check(
            default_res_copy,
            f'--{log_handler_name}-level', level,
        )

    # TODO patch print_usage
    # incorrect level
    level = 'somelevel'
    with pytest.raises(errors.ProvisionerCliError):
        _parse_args(
            f'--{log_handler_name}-level', level, add_version=True
        )


@pytest.mark.skip(reason="EOS-18738")
def test_cli_parser_logging_formatter(default_res_copy, log_handler_name):
    for formatter in prvsnr_config.logging['formatters']:
        default_res_copy.kwargs[f'{log_handler_name}_formatter'] = formatter
        check(
            default_res_copy,
            f'--{log_handler_name}-formatter', formatter,
        )

    # TODO patch print_usage
    # incorrect formatter
    formatter = 'someformatter'
    with pytest.raises(errors.ProvisionerCliError):
        _parse_args(
            f'--{log_handler_name}-formatter', formatter, add_version=True
        )


# TODO IMPROVE
@pytest.mark.skip(
    reason='requires improvement: capture writes to stderr/stdout'
)
@pytest.mark.parametrize("output_type", config.PRVSNR_CLI_OUTPUT)
def test_cli_parser_no_print_for_machine_output(
    default_res_copy, output_type, mocker
):
    # TODO patch print_usage
    # TODO patch print_help

    print_mock = mocker.spy(builtins, 'print')

    with pytest.raises(errors.ProvisionerCliError):
        _parse_args(
            '--some-options', add_version=False
        )

    assert print_mock.call_count == (
        0 if output_type in config.PRVSNR_CLI_MACHINE_OUTPUT else 1
    )

    print_mock.reset_mock()
