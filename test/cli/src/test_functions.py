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

import os
import pytest
import json
import yaml
import functools

import logging

import test.helper as h
from .helper import run_script as _run_script

logger = logging.getLogger(__name__)


CORTX_RELEASE_TEST_TAG = 'Cortx-1.0.0-PI.3-sprint11'

# TODO
#   - a way (marker) to split tests into groups:
#       - ones that are isolated (and can be run concurrently,
#         e.g. using pytest-xdist)
#       - and others that require serial execution
#     (pytest doesn't support that for now:
#       - https://github.com/pytest-dev/pytest-xdist/issues/18\
#       - https://github.com/pytest-dev/pytest-xdist/issues/84)
#


@pytest.fixture(scope='module')
def env_level():
    return 'base'


# TODO EOS-3247 remove
@pytest.fixture
def host_ssh_config(mhost):
    fpath = mhost.tmpdir / 'ssh_config'
    mhost.check_output("touch {}".format(fpath))
    return fpath


@pytest.fixture
def run_script(mlocalhost, tmpdir_function, request):

    def _f(
        test_content, *args, mhost=None, trace=False, stderr_to_stdout=True
    ):
        if mhost is None:
            mhost = request.getfixturevalue('mhost')

        script_path = (mhost.repo / 'cli/src/functions.sh')

        test_script_name = 'test_script.sh'
        test_script_path = tmpdir_function / test_script_name
        test_script_path.write_text(
            "set -e\n. {}\n{}\n{}"
            .format(script_path, 'verbosity=2' if trace else '', test_content)
        )

        if mhost is not mlocalhost:
            host_script_path = mhost.tmpdir / test_script_name
            mlocalhost.check_output(
                "scp -F {0} {1} {2}:{3}".format(
                    mhost.ssh_config,
                    test_script_path,
                    mhost.hostname,
                    host_script_path
                )
            )
            test_script_path = host_script_path

        return _run_script(
            mhost, test_script_path, *args,
            trace=trace,
            stderr_to_stdout=stderr_to_stdout
        )

    return _f


@pytest.fixture
def parse_args(run_script):

    def _f(
        *args,
        before_script='',
        after_script='',
        add_opts="''",
        add_long_opts="''",
        opts_cb="''",
        positional_args_cb="''",
        trace=False,
    ):
        return run_script(
            """
                {}
                parse_args {} {} {} {} {}
                {}
            """.format(
                before_script,
                add_opts,
                add_long_opts,
                opts_cb,
                positional_args_cb,
                ' '.join([*args]),
                after_script
            ),
            trace=trace
        )

    return _f


@pytest.fixture
def build_command(run_script):

    def _f(*args, trace=False):
        return run_script(
            """
                echo "cmd=<$(build_command {})>"
            """.format(
                ' '.join([*args])
            ),
            trace=trace
        )

    return _f


def test_functions_log_fails_for_wrong_level(run_script):
    level = 'some_bad_level'
    script = "log {} message".format(level)
    res = run_script(script, stderr_to_stdout=False)
    assert res.rc == 5
    # TODO IMPROVE use regex
    assert "ERROR: {}".format(level) in res.stderr
    assert "Unknown log level: {}".format(level) in res.stderr


def test_functions_log_levels(run_script):
    # TODO test log helpers

    levels_visibility = {
        'trace': 2,
        'debug': 1,
        'info': 0,
        'warn': 0,
        'error': 0
    }
    message = 'some-message'

    for verbosity in (0, 1, 2):
        for level in levels_visibility:
            script = """
                verbosity={0}
                log {1} {2}
                l_{1} {2}
            """.format(verbosity, level, message)
            res = run_script(script, stderr_to_stdout=False)
            assert res.rc == 0
            if levels_visibility[level] > verbosity:
                assert res.stdout == ''
            else:
                stream = (
                    res.stderr if level in ('warn', 'error') else res.stdout
                )
                # TODO IMPROVE
                _level = ('warning' if level == 'warn' else level)
                assert stream.count("{}".format(_level.upper())) == (
                    1 if level in ('warn', 'error') and verbosity == 2 else 2
                )
                assert stream.count("{}".format(message)) == (
                    10 if level in ('warn', 'error') and verbosity == 2 else 2
                )


def test_functions_log_helpers(run_script):
    # TODO test log helpers

    levels_visibility = {
        'trace': 2,
        'debug': 1,
        'info': 0,
        'warn': 0,
        'error': 0
    }
    message = 'some-message'

    for verbosity in (0, 1, 2):
        for level in levels_visibility:
            script = """
                verbosity={}
                log {} {}
            """.format(verbosity, level, message)
            res = run_script(script, stderr_to_stdout=False)
            assert res.rc == 0
            if levels_visibility[level] > verbosity:
                assert res.stdout == ''
            else:
                stream = (
                    res.stderr if level in ('warn', 'error') else res.stdout
                ).split(os.linesep)
                level = ('warning' if level == 'warn' else level)
                # TODO IMPROVE use regex
                assert level.upper() in stream[-2]
                assert message in stream[-2]


def test_functions_parse_args_succeeds_for_help(parse_args):
    for arg in ('-h',  '--help'):
        assert parse_args(arg).rc == 0


def test_functions_parse_args_fails_due_to_unknown_arg(parse_args):
    assert parse_args('--unknown-arg').rc == 2


def test_functions_parse_args_fails_due_to_bad_ssh_config(parse_args):
    for arg in ('-F',  '--ssh-config'):
        assert parse_args(arg).rc == 2
        assert parse_args(arg, '/tmp').rc == 5
        assert parse_args(arg, '/tmp/some-non-existent-file').rc == 5


def test_functions_parse_args_fails_due_to_missed_host_spec(parse_args):
    for arg in ('-r',  '--remote'):
        assert parse_args(arg).rc == 2


def test_functions_parse_args_parses_verbosity(parse_args):
    parse_args = functools.partial(
        parse_args, after_script='echo "verbosity=<$verbosity>"'
    )

    res = parse_args()
    assert res.rc == 0
    assert "verbosity=<0>" in res.stdout

    for arg in ('-v', '--verbose'):
        res = parse_args(arg)
        assert res.rc == 0
        assert "verbosity=<1>" in res.stdout

    for arg in ('-vv', '-v -v', '-v --verbose', '--verbose --verbose'):
        res = parse_args(arg)
        assert res.rc == 0
        assert "verbosity=<2>" in res.stdout


def test_functions_parse_args_defaults(parse_args):
    res = parse_args(before_script="verbosity=1")
    assert res.rc == 0
    # disabled by EOS-2410
    # assert "dry-run=<false>" in res.stdout
    assert "remote=<>" in res.stdout
    assert "singlenode=<false>" in res.stdout
    assert "ssh-config=<>" in res.stdout
    # disabled by EOS-2410
    # assert "sudo=<false>" in res.stdout


@pytest.mark.skip(reason="EOS-2410")
def test_functions_parse_args_parses_dry_run(parse_args):
    for arg in ('-n', '--dry-run'):
        res = parse_args(arg, before_script="verbosity=1")
        assert res.rc == 0
        assert "dry-run=<true>" in res.stdout


@pytest.mark.skip(reason="obsolete")
def test_functions_parse_args_parses_singlenode(parse_args):
    for arg in ('-S', '--singlenode'):
        res = parse_args(arg, before_script="verbosity=1")
        assert res.rc == 0
        assert "singlenode=<true>" in res.stdout


def test_functions_parse_args_parses_remote(parse_args):
    hostspec = 'user@host'
    for arg in ('-r', '--remote'):
        res = parse_args(arg, hostspec, before_script="verbosity=1")
        assert res.rc == 0
        assert "remote=<{}>".format(hostspec) in res.stdout


def test_functions_parse_args_parses_ssh_config(parse_args, host_ssh_config):
    for arg in ('-F', '--ssh-config'):
        res = parse_args(
            arg, str(host_ssh_config), before_script="verbosity=1"
        )
        assert res.rc == 0
        assert "ssh-config=<{}>".format(host_ssh_config) in res.stdout


@pytest.mark.skip(reason="EOS-2410")
def test_functions_parse_args_parses_sudo(parse_args):
    for arg in ('-s', '--sudo'):
        res = parse_args(arg, before_script="verbosity=1")
        assert res.rc == 0
        assert "sudo=<true>" in res.stdout


def test_functions_custom_usage_might_be_defined(parse_args):
    before_script = """
        function usage {
            echo "Custom usage info"
        }
    """

    res = parse_args('--help', before_script=before_script)
    assert res.rc == 0
    assert "Custom usage info" in res.stdout


def test_functions_base_options_usage(run_script):
    test_content = 'echo "$base_options_usage"'

    res = run_script(test_content)
    assert res.rc == 0

    for opt in (
        # disabled by EOS-2410 and later changes
        # '-n,  --dry-run',
        '-h,  --help',
        # '-r,  --remote [user@]hostname',
        # '-S,  --singlenode',
        '-F,  --ssh-config FILE',
        # disabled by EOS-2410
        #  '-s,  --sudo',
        '-v,  --verbose'
    ):
        assert opt in res.stdout


def test_functions_parse_args_rejects_add_opt_without_required_argument(
    parse_args
):
    for arg in ('-a', '--add-opt'):
        res = parse_args(
            arg,
            add_opts='a:',
            add_long_opts='add-opt:',
        )
        assert res.rc == 2


def test_functions_parse_args_fails_when_no_cb_defined(parse_args):
    res = parse_args(
        '-a',
        add_opts='a',
        add_long_opts='add-opt',
        opts_cb="''"
    )
    assert res.rc == 4
    assert 'Options parser callback is not defined' in res.stdout


def test_functions_parse_args_passes_fails_in_opts_cb(parse_args):
    before_script = """
        function parse_add_cb {
            exit 55
        }
    """
    res = parse_args(
        '-a',
        add_opts='a',
        opts_cb='parse_add_cb',
        before_script=before_script
    )
    assert res.rc == 55


def test_functions_parse_args_add_option_without_argument(parse_args):
    before_script = """
        add=false

        function parse_add_cb {
            case "$1" in
                -a|--add-opt)
                    add=true
                    ;;
                *)
                    >&2 echo "Unexpected option: $1"
                    exit 55
            esac
        }
    """

    after_script = "echo \"add=<$add>\""

    # good case
    for arg in ('-a', '--add-opt'):
        res = parse_args(
            arg,
            add_opts='a',
            add_long_opts='add-opt',
            opts_cb='parse_add_cb',
            before_script=before_script,
            after_script=after_script,
        )
        assert res.rc == 0
        assert "add=<true>" in res.stdout


def test_functions_parse_args_add_option_with_argument(parse_args):
    before_script = """
        add=
        dd=false


        function parse_add_cb {
            case "$1" in
                -a|--add-opt)
                    add="$2"
                    ;;
                -d|--dd-opt)
                    dd=true
                    ;;
                *)
                    >&2 echo "Unknown option: $1"
                    exit 55
            esac
        }
    """

    after_script = "echo \"add=<$add> dd=<$dd>\""

    for arg in ('-a', '--add-opt'):
        res = parse_args(
            arg, 'some-value', '--dd-opt',
            add_opts='a:A',
            add_long_opts='add-opt:,dd-opt',
            opts_cb='parse_add_cb',
            before_script=before_script,
            after_script=after_script
        )
        assert res.rc == 0
        assert "add=<some-value>" in res.stdout
        assert "dd=<true>" in res.stdout


def test_functions_parse_args_calls_fails_when_positional_args_cb_is_missed_for_args(parse_args):  # noqa: E501
    res = parse_args('arg1')
    assert res.rc == 2
    assert 'positional arguments are not expected' in res.stdout


def test_functions_parse_args_passes_fails_in_positional_args_cb(parse_args):
    before_script = """
        function positional_args_cb {
            exit 77
        }
    """

    res = parse_args(
        positional_args_cb='positional_args_cb',
        before_script=before_script,
    )
    assert res.rc == 77


@pytest.mark.skip('obsolete')
def test_functions_parse_args_calls_positional_args_cb(parse_args):
    before_script = """
        function positional_args_cb {
            echo "positional_args=<$@>"
        }
    """

    res = parse_args(
        positional_args_cb='positional_args_cb',
        before_script=before_script,
    )
    assert res.rc == 0
    assert "positional_args=<>" in res.stdout

    res = parse_args(
        'arg1 --sudo arg2 -S arg3 -vv',
        before_script=before_script,
        positional_args_cb='positional_args_cb',
    )
    assert res.rc == 0
    assert "positional_args=<arg1 arg2 arg3>" in res.stdout


def test_functions_build_command(build_command, host_ssh_config):
    res = build_command()
    assert res.rc == 0
    assert "cmd=<>" in res.stdout

    res = build_command("'' '' true")
    assert res.rc == 0
    assert "cmd=<sudo>" in res.stdout

    res = build_command("user@host ''")
    assert res.rc == 0
    assert "cmd=<ssh user@host>" in res.stdout

    # ssh-config is ignored if remote is not specified
    res = build_command("'' {}".format(host_ssh_config))
    assert res.rc == 0
    assert "cmd=<>" in res.stdout

    res = build_command("user@host {}".format(host_ssh_config))
    assert res.rc == 0
    assert "cmd=<ssh -F {} user@host>".format(host_ssh_config) in res.stdout

    res = build_command("user@host {} true".format(host_ssh_config))
    assert res.rc == 0
    assert (
        "cmd=<ssh -t -F {} user@host sudo>".format(host_ssh_config)
        in res.stdout
    )


def test_functions_hostname_from_spec(run_script):
    res = run_script('echo "res=<$(hostname_from_spec user@)>"')
    assert res.rc == 0
    assert "res=<>" in res.stdout

    res = run_script('echo "res=<$(hostname_from_spec hostname)>"')
    assert res.rc == 0
    assert "res=<hostname>" in res.stdout

    res = run_script('echo "res=<$(hostname_from_spec user@hostname)>"')
    assert res.rc == 0
    assert "res=<hostname>" in res.stdout


def test_functions_check_host_in_ssh_config(run_script, mhost):
    host_ssh_config = mhost.tmpdir / 'ssh-config'
    script = """
        if [[ -n "$(check_host_in_ssh_config {0} {1})" ]]; then
            echo {0} found
        else
            echo {0} not found
        fi
    """
    mhost.check_output(
        "echo -e 'Host host1\n\tHost host2' >{}".format(host_ssh_config)
    )

    res = run_script(script.format('host1', host_ssh_config))
    assert res.rc == 0
    assert "host1 found" in res.stdout

    res = run_script(script.format('host2', host_ssh_config))
    assert res.rc == 0
    assert "host2 not found" in res.stdout

    res = run_script(script.format('host3', host_ssh_config))
    assert res.rc == 0
    assert "host3 not found" in res.stdout


# TODO
#   - remote case is better to test from within virtual env as well
#   - other cases: ip missed, ifconfig missed, hostname is 127.0.0.1
@pytest.mark.isolated
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_collect_addrs(
    run_script, mhost, mlocalhost,
    ssh_config, remote, project_path,
    request
):
    meta = mlocalhost if remote else mhost
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"

    script = """
        collect_addrs {} {} true
    """.format(hostspec, ssh_config)

    res = run_script(script, mhost=meta, stderr_to_stdout=False)
    assert res.rc == 0
    collected = res.stdout.strip().split()

    expected = [mhost.hostname]
    assert set(collected) == set(expected)

    script = """
        collect_addrs {} {}
    """.format(hostspec, ssh_config)

    res = run_script(script, mhost=meta, stderr_to_stdout=False)
    assert res.rc == 0
    collected = res.stdout.strip().split()

    ifaces = mhost.check_output(
        "ip link show up | grep -v -i loopback | sed -n 's/^[0-9]\\+: \\([^:@]\\+\\).*/\\1/p'"  # noqa: E501
    )

    # Note. will include ip6 as well
    for interface in ifaces.strip().split(os.linesep):
        # TODO verify that it will work for all cases
        expected += [
            addr for addr in mhost.host.interface(interface).addresses
            if ':' not in addr
        ]

    assert set(collected) == set(expected)


@pytest.mark.isolated
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_check_host_reachable(
    run_script, mhost, mlocalhost,
    ssh_config, remote, project_path,
    request
):
    _mhost = mlocalhost if remote else mhost
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"

    host_ips = mhost.host.interface(mhost.interface).addresses

    for dest in host_ips + [mhost.hostname]:
        script = """
            check_host_reachable {} {} {}
        """.format(dest, hostspec, ssh_config)
        res = run_script(script, mhost=_mhost)
        assert res.rc == 0
        assert res.stdout == dest

    for dest in ['1.2.3.4', 'some-domain']:
        script = """
            check_host_reachable {} {} {}
        """.format(dest, hostspec, ssh_config)
        res = run_script(script, mhost=_mhost)
        assert res.rc == 0
        assert not res.stdout


# TODO
#   - multiplte names case (need multiple ifaces reachable between nodes)
#   - case when some interface is not shared between them
#   - case when they have the same IP in some non-shared interface
#     (vbox only case for now)
#   - actually we don't need cortx specific here, just two hosts
@pytest.mark.isolated
@pytest.mark.hosts(['srvnode1', 'srvnode2'])
@pytest.mark.parametrize(
    "local",
    ['srvnode1', 'srvnode2', None],
    ids=['run_on_itself', 'run_on_target', 'run_on_other']
)
def test_functions_get_reachable_names(
    run_script, mhostsrvnode1, mhostsrvnode2,
    mlocalhost, ssh_config, local, project_path,
    inject_ssh_config, request
):
    if local is None:
        mhost = mlocalhost
        hostspec1 = mhostsrvnode1.hostname
        hostspec2 = mhostsrvnode2.hostname
        _ssh_config = ssh_config
    else:
        _ssh_config = inject_ssh_config[local]
        if local == 'srvnode1':
            mhost = mhostsrvnode1
            hostspec1 = "''"
            hostspec2 = mhostsrvnode2.hostname
        else:
            mhost = mhostsrvnode2
            hostspec1 = mhostsrvnode1.hostname
            hostspec2 = "''"

    script = """
        get_reachable_names {} {} {}
    """.format(hostspec1, hostspec2, _ssh_config)

    res = run_script(
        script,
        mhost=mhost,
        stderr_to_stdout=False
    )
    assert res.rc == 0

    collected = res.stdout.split()
    assert collected

    host1_addrs = h.collect_ip4_addrs(mhostsrvnode1.host)
    host2_addrs = h.collect_ip4_addrs(mhostsrvnode2.host)
    common_addrs = set(host1_addrs) & set(host2_addrs)

    assert not (set(collected) & common_addrs)


# TODO check key for saltstack repo is imported
@pytest.mark.isolated
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_install_repos(
    run_script, mhost, mlocalhost,
    ssh_config, remote, project_path
):
    yum_repos_path = '/etc/yum.repos.d'
    vanilla_repos_hash = h.hash_dir(yum_repos_path, mhost.host)

    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    script = """
        install_repos {} {} {}
    """.format(hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    assert (
        h.hash_dir(yum_repos_path + '.bak', mhost.host) ==
        vanilla_repos_hash
    )

    local_repos_path = project_path / 'files/etc/yum.repos.d'
    try:
        assert (
            h.hash_dir(yum_repos_path, mhost.host) ==
            h.hash_dir(local_repos_path)
        )
    except AssertionError:
        remote_list = h.list_dir(yum_repos_path, mhost.host)
        local_list = h.list_dir(local_repos_path)
        assert remote_list == local_list
        raise

    # install for the second time and check that
    # it warns regarding backup creation skip
    res = run_script(
        script,
        mhost=(mlocalhost if remote else mhost),
        stderr_to_stdout=False
    )
    assert res.rc == 0
    assert 'WARNING: skip backup creation' in res.stderr


# relates to EOS-3247
@pytest.mark.skip(reason='likely outdated')
@pytest.mark.isolated
@pytest.mark.env_level('repos-installed')
def test_functions_systemd_libs_not_from_updates(mhost):
    res = mhost.check_output(
        'yum list all | grep systemd-libs'
    )
    # verify that no providers from updates repo
    # TODO might be not enough generic (e.g. updates might have other names)
    assert 'updates' not in res


# TODO actually utils env level is enough
@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("repo_src", ['unknown', 'github'])
def test_functions_install_provisioner(
    run_script, mhost, mlocalhost,
    ssh_config, remote, repo_src
):
    prvsnr_version = CORTX_RELEASE_TEST_TAG
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    script = """
        install_provisioner {} {} {} {} {}
    """.format(repo_src, prvsnr_version, hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))

    if repo_src == 'unknown':
        assert res.rc == 1
        assert 'ERROR: unsupported repo src' in res.stdout
    else:
        assert res.rc == 0

        # check repo files are in place
        for path in ('files', 'pillar', 'srv'):
            assert mhost.host.file(
                str(h.PRVSNR_REPO_INSTALL_DIR / path)
            ).exists


# TODO centos 7.6, 7.7
@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("version", [
    None,
    CORTX_RELEASE_TEST_TAG,
    'components/dev/centos-7.7.1908/provisioner/last_successful',
    'components/dev/centos-7.7.1908/provisioner/20'
], ids=[
    'default', 'tag', 'lastdev', 'somedev'
])
def test_functions_install_provisioner_rpm(
    run_script, mhost, mlocalhost,
    ssh_config, remote, version
):
    prvsnr_version = "''" if version is None else version
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    script = """
        install_provisioner rpm {} {} {} {}
    """.format(prvsnr_version, hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    assert mhost.host.package('cortx-prvsnr').is_installed
    assert mhost.host.package('python36-cortx-prvsnr').is_installed
    baseurl = mhost.check_output(
        'cat /etc/yum.repos.d/prvsnr.repo | grep baseurl'
    ).split('=')[1]
    assert baseurl == (
        'http://cortx-storage.colo.seagate.com/releases/cortx/{}'
        .format(
            'integration/centos-7.7.1908/last_successful'
            if version is None else version
        )
    )


# TODO
#  - remote case is better to test from within virtual env as well
@pytest.mark.isolated
@pytest.mark.env_level('utils')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("version", [
    None,          # raw copy
    'headcommit',  # by commit
    'HEAD',
    CORTX_RELEASE_TEST_TAG  # by tag
])
def test_functions_install_provisioner_local(
    run_script, mhost, mlocalhost,
    ssh_config, remote, version, project_path,
    request
):
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    prvsnr_version = version
    if prvsnr_version is None:
        prvsnr_version = "''"
    elif prvsnr_version == 'headcommit':
        prvsnr_version = mlocalhost.check_output('git rev-parse HEAD')

    script = """
        install_provisioner local {} {} {} {}
    """.format(prvsnr_version, hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    # TODO ensure that it doesn't leave any temporary files

    if version is None:
        # check that it installs the whole repository directory
        excluded_dirs = ['-name "{}"'.format(d) for d in h.REPO_BUILD_DIRS]
        expected = mlocalhost.check_output(
            "cd {} && find . \\( {} \\) -prune -o -type f -printf '%P\n'"
            .format(project_path, ' -o '.join(excluded_dirs))
        ).split()

        installed = mhost.check_output(
            "find {} -type f -printf '%P\n'".format(h.PRVSNR_REPO_INSTALL_DIR)
        ).split()
    else:
        # check repo files are in place
        expected = mlocalhost.check_output(
            'git ls-tree --full-tree -r --name-only {}'.format(prvsnr_version)
        ).split()

        installed = mhost.check_output(
            "find {} -type f -printf '%P\n'".format(h.PRVSNR_REPO_INSTALL_DIR)
        ).split()

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)
    assert not diff_expected
    assert not diff_installed


@pytest.mark.isolated
@pytest.mark.env_level('utils')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "singlenode", [True, False], ids=['singlenode', 'cluster']
)
def test_functions_install_provisioner_proper_cluster_pillar(
    run_script, mhost, mlocalhost,
    ssh_config, remote, project_path, singlenode,
    request
):
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO
    is_singlenode = 'true' if singlenode else 'false'

    prvsnr_version = 'HEAD'

    script = """
        install_provisioner local {} {} {} {} {}
    """.format(prvsnr_version, hostspec, ssh_config, with_sudo, is_singlenode)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    source_path = h.PRVSNR_REPO_INSTALL_DIR / (
        'pillar/samples/singlenode.cluster.sls' if singlenode
        else 'pillar/samples/dualnode.cluster.sls'
    )
    dest_path = h.PRVSNR_REPO_INSTALL_DIR / 'pillar/components/cluster.sls'
    h.check_output(mhost, 'diff -us {} {}'.format(source_path, dest_path))


@pytest.mark.isolated
@pytest.mark.cortx_spec({'': {'minion_id': 'srvnode-1', 'roles': ['primary']}})
@pytest.mark.env_level('network-manager-installed')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "nm_installed", [True, False], ids=['nm_installed', 'nm_not_installed']
)
def test_functions_configure_network(
    run_script, mhost, mlocalhost,
    ssh_config, remote, nm_installed, project_path,
    install_provisioner
):
    if not nm_installed:
        mhost.check_output('yum remove -y NetworkManager')

    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    script = """
        configure_network {} {} {}
    """.format(hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    assert not mhost.host.package("NetworkManager").is_installed

    # TODO more stict checks for network files
    assert mhost.host.file('/etc/sysconfig/network-scripts/ifcfg-mgmt0').exists
    assert mhost.host.file('/etc/sysconfig/network-scripts/ifcfg-data0').exists

    host_hash = h.hash_file(
        '/etc/modprobe.d/bonding.conf', mhost.host
    )
    localhost_hash = h.hash_file(
        project_path / 'files/etc/modprobe.d/bonding.conf', mlocalhost.host
    )
    assert host_hash == localhost_hash


# TODO install_salt cases:
# - with sudo
# - do not use localhost for remote tests
@pytest.mark.isolated
@pytest.mark.env_level('repos-installed')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_install_salt(
    run_script, mhost, mlocalhost,
    ssh_config, remote, project_path
):
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    script = """
        install_salt {} {} {}
    """.format(hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    assert mhost.host.package("salt-minion").is_installed
    assert mhost.host.package("salt-master").is_installed


# TODO
#   - use different env for remote clients installation
#     instead of the localhost
#   - integration test for master-minion connected scheme
#     to check grains, minion-ids ...
@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.hosts(['srvnode1', 'srvnode2'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("primary", [True, False], ids=['master', 'minion'])
def test_functions_configure_salt(
    run_script, mlocalhost, ssh_config, remote, primary, project_path, request
):
    host_label = 'srvnode1' if primary else 'srvnode2'
    mhost = request.getfixturevalue('mhost' + host_label)
    _ = request.getfixturevalue('install_provisioner')

    minion_id = 'some-minion-id'
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO
    is_master = 'true' if primary else 'false'

    script = """
        configure_salt {} {} {} {} {}
    """.format(minion_id, hostspec, ssh_config, with_sudo, is_master)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    mhost.check_output(
        'diff -q {} /etc/salt/master'.format(
            h.PRVSNR_REPO_INSTALL_DIR /
            'srv/provisioner/salt_master/files/master'
        )
    )

    minion_config_source = (
        h.PRVSNR_REPO_INSTALL_DIR /
        'srv/provisioner/salt_minion/files/minion'
    )
    mhost.check_output(
        'sed -i "s/^master: .*/master: srvnode-1/g" {}'
        .format(minion_config_source)
    )
    mhost.check_output(
        'diff -q {} /etc/salt/minion'.format(minion_config_source)
    )
    assert mhost.check_output('cat /etc/salt/minion_id') == minion_id
    # TODO ensure that serviceses were actually restarted

    assert mhost.host.service('salt-minion').is_enabled
    assert mhost.host.service('salt-minion').is_running

    if primary:
        assert mhost.host.service('salt-master').is_enabled
        assert mhost.host.service('salt-master').is_running

    output = mhost.host.check_output(
        'salt-call --local --out json grains.items'
    )
    grains = json.loads(output)['local']
    assert 'roles' in grains
    assert grains['roles'] == ['primary'] if primary else ['secondary']
    assert grains['id'] == minion_id


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.cortx_spec({'': {'minion_id': 'srvnode-1', 'roles': ['primary']}})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "master_host",
    [None, 'some-master-host'],
    ids=['default_master', 'custom_master']
)
def test_functions_configure_salt_master_host(
    run_script, mhost, mlocalhost,
    ssh_config, remote, master_host, project_path,
    install_provisioner
):
    default_cortx_salt_master = 'srvnode-1'

    minion_id = 'some-minion-id'
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    _master_host = "''" if master_host is None else master_host

    script = """
        configure_salt {} {} {} {} false {}
    """.format(minion_id, hostspec, ssh_config, with_sudo, _master_host)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    output = mhost.check_output(
        'salt-call --local --out json config.get master'
    )
    output = json.loads(output)
    assert output['local'] == (
        default_cortx_salt_master if master_host is None else master_host
    )


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.cortx_spec(
    {'': {'minion_id': 'some-minion-id', 'roles': ['primary']}}
)
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_accept_salt_key_singlenode(
    run_script, mhost, mlocalhost,
    ssh_config, remote, project_path,
    install_provisioner
):
    minion_id = 'some-minion-id'
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO
    is_master = 'true'

    script = """
        configure_salt {} {} {} {} {} localhost
    """.format(minion_id, hostspec, ssh_config, with_sudo, is_master)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    script = """
        accept_salt_key {} {} {} {}
    """.format(minion_id, hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0

    # check that the minion's key is accepted
    output = mhost.check_output("salt-key --out json --list all")
    output = json.loads(output)
    assert output['minions'] == [minion_id]

    # check that the minion is started
    output = mhost.check_output("salt-run --out json manage.present")
    output = json.loads(output)
    assert output == [minion_id]

    # TODO
    #    - separate test
    #    - more cases to cover: already rejected, denied
    # check how it works for already accepted key
    script = """
        accept_salt_key {} {} {} {}
    """.format(minion_id, hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))
    assert res.rc == 0
    assert (
        "INFO: no key acceptance is needed for minion {}"
        .format(minion_id) in res.stdout
    )


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.hosts(['srvnode1', 'srvnode2'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_accept_salt_key_cluster(
    run_script, mhostsrvnode1, mhostsrvnode2,
    mlocalhost, ssh_config, remote, project_path,
    install_provisioner, cortx_spec
):
    srvnode1_minion_id = cortx_spec['srvnode1']['minion_id']
    srvnode2_minion_id = cortx_spec['srvnode2']['minion_id']
    with_sudo = 'false'  # TODO

    salt_server_ip = mhostsrvnode1.host.interface(
        mhostsrvnode1.interface
    ).addresses[0]

    # configure srvnode-1
    script = """
        configure_salt {0} {1} '' {2} true localhost
    """.format(
        srvnode1_minion_id,
        salt_server_ip,
        with_sudo
    )
    res = run_script(script, mhost=mhostsrvnode1)
    assert res.rc == 0

    # configure srvnode-2
    script = """
        configure_salt {} '' '' {} false {}
    """.format(
        srvnode2_minion_id, with_sudo, salt_server_ip
    )
    res = run_script(script, mhost=mhostsrvnode2)
    assert res.rc == 0

    hostspec = mhostsrvnode1.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"

    for _id in (srvnode1_minion_id, srvnode2_minion_id):
        script = """
            accept_salt_key {} {} {} {}
        """.format(
            _id, hostspec, ssh_config, with_sudo
        )
        res = run_script(
            script, mhost=(mlocalhost if remote else mhostsrvnode1)
        )
        assert res.rc == 0

    output = mhostsrvnode1.check_output("salt-key --out json --list all")
    output = json.loads(output)
    assert (
        set(output['minions']) ==
        set([srvnode1_minion_id, srvnode2_minion_id])
    )


# Note. 'salt-installed' is used since it has python3.6 installed
# (TODO might need to improve)
@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.cortx_spec({'': {'minion_id': 'srvnode-1', 'roles': ['primary']}})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "component",
    [
        'cluster',
        # 'motr',  # TODO EOS-5940
        # 'haproxy',
        'release',
        's3clients',
        # 's3server',
        'sspl'
    ]
)
def test_functions_cortx_pillar_show_skeleton(
    run_script, mhost, mlocalhost,
    ssh_config, remote, component, project_path,
    install_provisioner
):
    h.install_provisioner_api(mhost)

    # 1. get pillar to compare
    # TODO python3.6 ???
    pillar_content = mhost.check_output(
        f"provisioner configure_cortx {component} --show"
    )

    # 2. call the script
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    script = """
        cortx_pillar_show_skeleton {} {} {} {}
    """.format(component, hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))

    # 3. verify
    assert res.rc == 0
    assert res.stdout.strip() == pillar_content


@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.cortx_spec({'': {'minion_id': 'srvnode-1', 'roles': ['primary']}})
def test_functions_cortx_pillar_update_fail(
    run_script, mhost, ssh_config, install_provisioner
):
    res = run_script('cortx_pillar_update cluster some-path', mhost=mhost)
    assert res.rc == 1
    assert 'ERROR: not a file' in res.stdout


# TODO
#   - 'salt-installed' is used since it has python3.6 installed,
#      python and repo installed would be enough actually
#   - do we need to test all components actually,
#     might be a subject of other test (e.g. for utils)
#   - update and load default are related to each other but anyway makes sense
#     to split into separate tests
@pytest.mark.isolated
@pytest.mark.env_level('salt-installed')
@pytest.mark.cortx_spec({'': {'minion_id': 'srvnode-1', 'roles': ['primary']}})
@pytest.mark.mock_cmds({'': ['salt']})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "component",
    [
        'cluster',
        # 'motr',  TODO EOS-5940
        # 'haproxy',
        'release',
        's3clients'
    ]
    # Removed s3server and sspl EOS-4907
)
def test_functions_cortx_pillar_update_and_load_default(
    run_script, mhost, mlocalhost, tmpdir_function,
    ssh_config, remote, component, project_path,
    install_provisioner, mock_hosts
):
    pillar_new_key = 'test'

    h.install_provisioner_api(mhost)
    # 1. prepare some valid pillar for the component
    # TODO python3.6 ???
    new_pillar_content = mhost.check_output(
        f"provisioner configure_cortx {component} --show"
    )
    new_pillar_dict = yaml.safe_load(new_pillar_content.strip())
    new_pillar_dict.update({pillar_new_key: "temporary"})

    component_pillar = '{}.sls'.format(component)
    tmp_file = tmpdir_function / component_pillar
    tmp_file.write_text(
        yaml.dump(new_pillar_dict, default_flow_style=False, canonical=False)
    )
    if not remote:
        host_tmp_file = mhost.tmpdir / component_pillar
        mlocalhost.check_output(
            "scp -F {0} {1} {2}:{3}".format(
                ssh_config,
                tmp_file,
                mhost.hostname,
                host_tmp_file
            )
        )
        tmp_file = host_tmp_file

    # 2. call the update script
    hostspec = mhost.hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false'  # TODO

    script = """
        cortx_pillar_update {} {} {} {} {}
    """.format(component, tmp_file, hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))

    # 3. verify
    assert res.rc == 0

    tmp_file_content = (mlocalhost if remote else mhost).check_output(
        'cat {}'.format(tmp_file)
    )
    current_def_pillar = h.PRVSNR_PILLAR_DIR / 'components' / component_pillar
    current_user_pillar = h.PRVSNR_USER_PILLAR_ALL_HOSTS_DIR / component_pillar
    pillar_file_content = mhost.check_output(
        'cat {}'.format(current_user_pillar)
    )

    tmp_file_dict = yaml.safe_load(tmp_file_content)
    pillar_file_dict = yaml.safe_load(pillar_file_content)
    assert tmp_file_dict == pillar_file_dict

    # check that pillar has been refreshed on the minions
    expected_lines = [
        'SALT-ARGS: * saltutil.refresh_pillar'
    ]
    assert res.stdout.count('SALT-ARGS: ') == len(expected_lines)

    stdout_lines = res.stdout.split(os.linesep)
    ind = stdout_lines.index(expected_lines[0])
    assert stdout_lines[ind:(ind + len(expected_lines))] == expected_lines

    # 4. call the script to reset to defaults
    script = """
        cortx_pillar_load_default {} {} {} {}
    """.format(component, hostspec, ssh_config, with_sudo)

    res = run_script(script, mhost=(mlocalhost if remote else mhost))

    # 5. verify
    assert res.rc == 0

    pillar_file_content = mhost.check_output(
        'cat {}'.format(current_def_pillar)
    )
    pillar_file_dict = yaml.safe_load(pillar_file_content)
    del new_pillar_dict[pillar_new_key]
    assert new_pillar_dict == pillar_file_dict

    assert res.stdout.count('SALT-ARGS: ') == len(expected_lines)

    stdout_lines = res.stdout.split(os.linesep)
    ind = stdout_lines.index(expected_lines[0])
    assert stdout_lines[ind:(ind + len(expected_lines))] == expected_lines
