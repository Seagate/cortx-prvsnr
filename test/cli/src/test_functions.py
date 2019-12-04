import os
import pytest
import json
import yaml
import functools
from pathlib import Path

import logging
import testinfra

import test.helper as h

logger = logging.getLogger(__name__)

DEFAULT_SCRIPT_PATH = "/tmp/functions.sh"

# TODO
#   - a way (marker) to split tests into groups:
#       - ones that are isolated (and can be run concurrently, e.g. using pytest-xdist)
#       - and others that require serial execution
#     (pytest doesn't support that for now:
#       - https://github.com/pytest-dev/pytest-xdist/issues/18\
#       - https://github.com/pytest-dev/pytest-xdist/issues/84)
#


@pytest.fixture(scope='module')
def env_name():
    return 'centos7-base'


@pytest.fixture(scope='module')
def local_script_path(project_path):
    return str(project_path / 'cli/src/functions.sh')


@pytest.fixture(scope='module')
def post_host_run_hook(localhost, local_script_path):
    def f(host, hostname, ssh_config, request):
        localhost.check_output(
            "scp -F {} {} {}:{}".format(
                ssh_config,
                local_script_path,
                hostname,
                DEFAULT_SCRIPT_PATH
            )
        )
    return f


@pytest.fixture
def host_ssh_config(host, host_tmpdir):
    fpath = host_tmpdir / 'ssh_config'
    host.check_output("touch {}".format(fpath))
    return fpath


@pytest.fixture
def run_script(localhost, tmp_path, ssh_config, request):

    def _f(
        test_content, trace=False, host=None, host_tmpdir=None,
        script_path=DEFAULT_SCRIPT_PATH, stderr_to_stdout=True
    ):
        host = request.getfixturevalue('host') if host is None else host
        host_tmpdir = request.getfixturevalue('host_tmpdir') if host_tmpdir is None else host_tmpdir
        hostname = host.check_output('hostname')

        test_script_name = 'test_script.sh'
        test_script_path = tmp_path / test_script_name
        test_script_path.write_text(
            "set -e\n. {}\n{}\n{}"
            .format(script_path, 'verbosity=2' if trace else '', test_content)
        )

        if host is not localhost:
            host_script_path = host_tmpdir / test_script_name
            localhost.check_output(
                "scp -F {0} {1} {2}:{3}".format(
                    ssh_config,
                    test_script_path,
                    hostname,
                    host_script_path
                )
            )
            test_script_path = host_script_path

        return h.run(
            host, (
                "bash {} {} {}"
                .format(
                    '-x' if trace else '',
                    test_script_path,
                    '2>&1' if stderr_to_stdout else ''
                )
            ), force_dump=trace
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
    assert res.stderr == "ERROR: Unknown log level: {}\n".format(level)


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
                _level = ('warning' if level == 'warn' else level)
                assert stream.count("{}: {}\n".format(_level.upper(), message)) == 2


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
                )
                level = ('warning' if level == 'warn' else level)
                assert "{}: {}".format(level.upper(), message) in stream.split(os.linesep)


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
        res = parse_args(arg, str(host_ssh_config), before_script="verbosity=1")
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
        # disabled by EOS-2410
        # '-n,  --dry-run',
        '-h,  --help',
        '-r,  --remote [user@]hostname',
        '-S,  --singlenode',
        '-F,  --ssh-config FILE',
        # disabled by EOS-2410
        #  '-s,  --sudo',
        '-v,  --verbose'
    ):
        assert opt in res.stdout


def test_functions_parse_args_rejects_add_opt_without_required_argument(parse_args):
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


def test_functions_parse_args_calls_fails_when_positional_args_cb_is_missed_for_args(parse_args):
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
    assert "cmd=<ssh -t -F {} user@host sudo>".format(host_ssh_config) in res.stdout


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


def test_functions_check_host_in_ssh_config(run_script, host, host_tmpdir):
    host_ssh_config = host_tmpdir / 'ssh-config'
    script = """
        if [[ -n "$(check_host_in_ssh_config {0} {1})" ]]; then
            echo {0} found
        else
            echo {0} not found
        fi
    """
    host.check_output("echo -e 'Host host1\n\tHost host2' >{}".format(host_ssh_config))

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
@pytest.mark.env_name('centos7-base')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_collect_addrs(
    run_script, host, hostname, localhost,
    ssh_config, remote, project_path,
    request
):
    _host = localhost if remote else host
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"

    if remote is True:
        script_path = project_path / 'cli' / 'src' / 'functions.sh'
    else:
        script_path = DEFAULT_SCRIPT_PATH

    script = """
        verbosity=2
        collect_addrs {} {}
    """.format(hostspec, ssh_config)

    res = run_script(script, host=_host, script_path=script_path, stderr_to_stdout=False)
    assert res.rc == 0

    collected = res.stdout.strip().split()
    expected = [hostname]

    ifaces = host.check_output(
        "ip link show up | grep -v -i loopback | sed -n 's/^[0-9]\\+: \\([^:@]\\+\\).*/\\1/p'"
    )

    # Note. will include ip6 as well
    for iface in ifaces.strip().split(os.linesep):
        # TODO verify that it will work for all cases
        expected += [
            addr for addr in host.interface(iface).addresses
            if ':' not in addr
        ]

    assert set(collected) == set(expected)


@pytest.mark.isolated
@pytest.mark.env_name('centos7-base')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_check_host_reachable(
    run_script, host, hostname, localhost,
    ssh_config, remote, project_path, host_meta,
    request
):
    _host = localhost if remote else host
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"

    if remote is True:
        script_path = project_path / 'cli' / 'src' / 'functions.sh'
    else:
        script_path = DEFAULT_SCRIPT_PATH

    host_ips = host.interface(host_meta.iface).addresses

    for dest in host_ips + [hostname]:
        script = """
            check_host_reachable {} {} {}
        """.format(dest, hostspec, ssh_config)
        res = run_script(script, host=_host, script_path=script_path)
        assert res.rc == 0
        assert res.stdout == dest

    for dest in ['1.2.3.4', 'some-domain']:
        script = """
            check_host_reachable {} {} {}
        """.format(dest, hostspec, ssh_config)
        res = run_script(script, host=_host, script_path=script_path)
        assert res.rc == 0
        assert not res.stdout


# TODO actually utils env level is enough for all except 'rpm'
@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("repo_src", ['unknown', 'rpm', 'gitlab'])
def test_functions_install_provisioner(
    run_script, host, hostname, localhost,
    ssh_config, remote, repo_src, project_path
):
    prvsnr_version = 'ees1.0.0-PI.2-sprint7'
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO
    # TODO imporove
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        install_provisioner {} {} {} {} {}
    """.format(repo_src, prvsnr_version, hostspec, ssh_config, with_sudo)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)

    if repo_src == 'unknown':
        assert res.rc == 1
        assert 'ERROR: unsupported repo src' in res.stdout
    else:
        assert res.rc == 0

        # TODO some more strict checks
        if repo_src == 'rpm':
            assert host.package('eos-prvsnr').is_installed

        # check repo files are in place
        for path in ('files', 'pillar', 'srv'):
            assert host.file(str(h.PRVSNR_REPO_INSTALL_DIR / path)).exists


# TODO
#  - remote case is better to test from within virtual env as well
#  - by tag
@pytest.mark.isolated
@pytest.mark.env_name('centos7-utils')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("version", [None, 'headcommit', 'HEAD'])
def test_functions_install_provisioner_local(
    run_script, host, hostname, localhost,
    ssh_config, remote, version, project_path,
    request
):
    host_project_path = None
    if remote is True:
        script_path = project_path / 'cli' / 'src' / 'functions.sh'
    else:
        host_project_path = request.getfixturevalue('inject_repo')['host']
        script_path = host_project_path / 'cli/src/functions.sh'

    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO

    prvsnr_version = version
    if prvsnr_version is None:
        prvsnr_version = "''"
    elif prvsnr_version == 'headcommit':
        prvsnr_version = localhost.check_output('git rev-parse HEAD')

    script = """
        install_provisioner local {} {} {} {}
    """.format(prvsnr_version, hostspec, ssh_config, with_sudo)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0

    # TODO ensure that it doesn't leave any temporary files

    if version is None:
        # check that it installs the whole repository directory
        excluded_dirs = ['-name "{}"'.format(d) for d in h.REPO_BUILD_DIRS]
        expected = localhost.check_output(
            "cd {} && find . \\( {} \\) -prune -o -type f -printf '%P\n'"
            .format(project_path, ' -o '.join(excluded_dirs))
        ).split()

        installed = host.check_output(
            "find {} -type f -printf '%P\n'".format(h.PRVSNR_REPO_INSTALL_DIR)
        ).split()
    else:
        # check repo files are in place
        expected = localhost.check_output(
            'git ls-tree --full-tree -r --name-only {}'.format(prvsnr_version)
        ).split()

        installed = host.check_output(
            "find {} -type f -printf '%P\n'".format(h.PRVSNR_REPO_INSTALL_DIR)
        ).split()

    diff_expected = set(expected) - set(installed)
    diff_installed = set(installed) - set(expected)
    assert not diff_expected
    assert not diff_installed


@pytest.mark.isolated
@pytest.mark.env_name('centos7-utils')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("singlenode", [True, False], ids=['singlenode', 'cluster'])
def test_functions_install_provisioner_proper_cluster_pillar(
    run_script, host, hostname, localhost,
    ssh_config, remote, project_path, singlenode,
    request
):
    host_project_path = None
    if remote is True:
        script_path = project_path / 'cli' / 'src' / 'functions.sh'
    else:
        host_project_path = request.getfixturevalue('inject_repo')['host']
        script_path = host_project_path / 'cli/src/functions.sh'

    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO
    is_singlenode = 'true' if singlenode else 'false'

    prvsnr_version = 'HEAD'

    script = """
        install_provisioner local {} {} {} {} {}
    """.format(prvsnr_version, hostspec, ssh_config, with_sudo, is_singlenode)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0

    source_path = h.PRVSNR_REPO_INSTALL_DIR / (
        'pillar/components/samples/singlenode.cluster.sls' if singlenode
        else 'pillar/components/samples/ees.cluster.sls'
    )
    dest_path = h.PRVSNR_REPO_INSTALL_DIR / 'pillar/components/cluster.sls'
    h.check_output(host, 'diff -us {} {}'.format(source_path, dest_path))


@pytest.mark.isolated
@pytest.mark.eos_spec({'host': {'minion_id': 'eosnode-1', 'is_primary': True}})
@pytest.mark.env_name('centos7-network-manager-installed')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("nm_installed", [True, False], ids=['nm_installed', 'nm_not_installed'])
def test_functions_configure_network(
    run_script, host, hostname, localhost,
    ssh_config, remote, nm_installed, project_path,
    install_provisioner
):
    if not nm_installed:
        host.check_output('yum remove -y NetworkManager')

    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO
    # TODO imporove
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        configure_network {} {} {}
    """.format(hostspec, ssh_config, with_sudo)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0

    assert not host.package("NetworkManager").is_installed

    # TODO more stict checks for network files
    assert host.file('/etc/sysconfig/network-scripts/ifcfg-mgmt0').exists
    assert host.file('/etc/sysconfig/network-scripts/ifcfg-data0').exists

    # TODO check md5sum is everywhere available
    host_hash = host.check_output('md5sum /etc/modprobe.d/bonding.conf')
    localhost_hash = localhost.check_output('md5sum {}'.format(project_path / 'files/etc/modprobe.d/bonding.conf'))
    assert host_hash.split()[0] == localhost_hash.split()[0]


# TODO install_salt cases:
# - with sudo
# - do not use localhost for remote tests
@pytest.mark.isolated
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_install_salt(
    run_script, host, hostname, localhost,
    ssh_config, remote, project_path
):
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO
    # TODO imporove
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        install_salt {} {} {}
    """.format(hostspec, ssh_config, with_sudo)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0

    assert host.package("salt-minion").is_installed
    assert host.package("salt-master").is_installed


# TODO
#   - use different env for remote clients installation instead of the localhost
#   - integration test for master-minion connected scheme to check grains, minion-ids ...
@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.hosts(['host_eosnode1', 'host_eosnode2'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("master", [True, False], ids=['master', 'minion'])
def test_functions_configure_salt(
    run_script, localhost, ssh_config, remote, master, project_path, request
):
    host_label = 'eosnode1' if master else 'eosnode2'
    host = request.getfixturevalue('host_' + host_label)
    hostname = request.getfixturevalue('hostname_' + host_label)
    host_tmpdir = request.getfixturevalue('host_tmpdir_' + host_label)
    _ = request.getfixturevalue('install_provisioner')

    minion_id = 'some-minion-id'
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO
    is_master = 'true' if master else 'false'
    # TODO imporove
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        configure_salt {} {} {} {} {}
    """.format(minion_id, hostspec, ssh_config, with_sudo, is_master)

    res = run_script(
        script,
        host=(localhost if remote else host),
        host_tmpdir=host_tmpdir,
        script_path=script_path
    )
    assert res.rc == 0

    host.check_output(
        'diff -q {} /etc/salt/master'.format(
            h.PRVSNR_REPO_INSTALL_DIR / 'files/etc/salt/master'
        )
    )
    host.check_output(
        'diff -q {} /etc/salt/minion'.format(
            h.PRVSNR_REPO_INSTALL_DIR / 'files/etc/salt/minion'
        )
    )
    assert host.check_output('cat /etc/salt/minion_id') == minion_id
    # TODO ensure that serviceses were actually restarted

    assert host.service('salt-minion').is_enabled
    assert host.service('salt-minion').is_running

    if master:
        assert host.service('salt-master').is_enabled
        assert host.service('salt-master').is_running

    output = host.check_output('salt-call --local --out json grains.items')
    grains = json.loads(output)['local']
    assert 'roles' in grains
    assert grains['roles'] == ['primary'] if master else ['slave']
    assert grains['id'] == minion_id


@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.eos_spec({'host': {'minion_id': 'eosnode-1', 'is_primary': True}})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("master_host", [None, 'some-master-host'], ids=['default_master', 'custom_master'])
def test_functions_configure_salt_master_host(
    run_script, host, hostname, localhost,
    ssh_config, remote, master_host, project_path,
    install_provisioner
):
    default_eos_salt_master = 'eosnode-1'

    minion_id = 'some-minion-id'
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO

    _master_host = "''" if master_host is None else master_host

    # TODO improve
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        configure_salt {} {} {} {} false {}
    """.format(minion_id, hostspec, ssh_config, with_sudo, _master_host)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0

    output = host.check_output('salt-call --local --out json config.get master')
    output = json.loads(output)
    assert output['local'] == (
        default_eos_salt_master if master_host is None else master_host
    )


@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.eos_spec({'host': {'minion_id': 'some-minion-id', 'is_primary': True}})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_accept_salt_keys_singlenode(
    run_script, host, hostname, localhost,
    ssh_config, remote, project_path,
    install_provisioner
):
    minion_id = 'some-minion-id'
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO
    is_master = 'true'
    # TODO imporove
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        configure_salt {} {} {} {} {} localhost
    """.format(minion_id, hostspec, ssh_config, with_sudo, is_master)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0

    script = """
        accept_salt_keys {} {} {} {}
    """.format(minion_id, hostspec, ssh_config, with_sudo)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0

    # check that the minion's key is accepted
    output = host.check_output("salt-key --out json --list all")
    output = json.loads(output)
    assert output['minions'] == [minion_id]

    # check that the minion is started
    output = host.check_output("salt-run --out json manage.present")
    output = json.loads(output)
    assert output == [minion_id]

    # TODO
    #    - separate test
    #    - more cases to cover: already rejected, denied
    # check how it works for already accepted key
    script = """
        accept_salt_keys {} {} {} {}
    """.format(minion_id, hostspec, ssh_config, with_sudo)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0
    assert (
        "INFO: no key acceptance is needed for minion {}"
        .format(minion_id) in res.stdout
    )


@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.hosts(['host_eosnode1', 'host_eosnode2'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_accept_salt_keys_cluster(
    run_script, host_eosnode1, host_eosnode2, hostname_eosnode1,
    host_tmpdir_eosnode1, host_tmpdir_eosnode2,
    localhost, ssh_config, remote, project_path,
    install_provisioner, hosts_meta, eos_spec
):
    eosnode1_minion_id = eos_spec['host_eosnode1']['minion_id']
    eosnode2_minion_id = eos_spec['host_eosnode2']['minion_id']
    with_sudo = 'false' # TODO

    salt_server_ip = host_eosnode1.interface(hosts_meta['host_eosnode1'].iface).addresses[0]

    # configure eosnode-1
    script = """
        configure_salt {} '' '' {} true localhost
    """.format(
        eosnode1_minion_id, with_sudo, salt_server_ip
    )
    res = run_script(script, host=host_eosnode1, host_tmpdir=host_tmpdir_eosnode1)
    assert res.rc == 0

    # configure eosnode-2
    script = """
        configure_salt {} '' '' {} false {}
    """.format(
        eosnode2_minion_id, with_sudo, salt_server_ip
    )
    res = run_script(script, host=host_eosnode2, host_tmpdir=host_tmpdir_eosnode2)
    assert res.rc == 0

    hostspec = hostname_eosnode1 if remote else "''"
    ssh_config = ssh_config if remote else "''"
    # TODO improve
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        accept_salt_keys "{} {}" {} {} {}
    """.format(eosnode1_minion_id, eosnode2_minion_id, hostspec, ssh_config, with_sudo)

    res = run_script(
        script, host=(localhost if remote else host_eosnode1),
        host_tmpdir=host_tmpdir_eosnode1,
        script_path=script_path
    )
    assert res.rc == 0

    output = host_eosnode1.check_output("salt-key --out json --list all")
    output = json.loads(output)
    assert set(output['minions']) == set([eosnode1_minion_id, eosnode2_minion_id])

# Note. 'centos7-salt-installed' is used since it has python3.6 installed
# (TODO might need to improve)
@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.eos_spec({'host': {'minion_id': 'eosnode-1', 'is_primary': True}})
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "component",
    ['cluster', 'eoscore', 'haproxy', 'release', 's3client', 's3server', 'sspl']
)
def test_functions_eos_pillar_show_skeleton(
    run_script, host, hostname, host_tmpdir,
    localhost, tmp_path,
    ssh_config, remote, component, project_path,
    install_provisioner
):
    # 1. get pillar to compare
    # TODO python3.6 ???
    pillar_content = host.check_output(
        'python3.6 {0}/configure-eos.py {1} --show-{1}-file-format'.format(
            h.PRVSNR_REPO_INSTALL_DIR / 'cli' / 'utils', component
        )
    )

    # 2. call the script
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO
    # TODO improve
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        eos_pillar_show_skeleton {} {} {} {}
    """.format(component, hostspec, ssh_config, with_sudo)

    res = run_script(
        script, host=(localhost if remote else host), script_path=script_path
    )

    # 3. verify
    assert res.rc == 0
    assert res.stdout.strip() == pillar_content


@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.eos_spec({'host': {'minion_id': 'eosnode-1', 'is_primary': True}})
def test_functions_eos_pillar_update_fail(
    run_script, host, ssh_config, install_provisioner
):
    res = run_script('eos_pillar_update cluster some-path', host=host)
    assert res.rc == 1
    assert 'ERROR: not a file' in res.stdout


# TODO
#   - 'centos7-salt-installed' is used since it has python3.6 installed,
#      python and repo installed would be enough actually
#   - do we need to test all components actually, might be a subject of other test
#     (e.g. for utils)
#   - update and load default are related to each other but anyway makes sense
#     to split into separate tests
@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.eos_spec({'host': {'minion_id': 'eosnode-1', 'is_primary': True}})
@pytest.mark.mock_cmds(['salt'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "component",
    ['cluster', 'eoscore', 'haproxy', 'release', 's3client', 's3server', 'sspl']
)
def test_functions_eos_pillar_update_and_load_default(
    run_script, host, hostname, host_tmpdir,
    localhost, tmp_path,
    ssh_config, remote, component, project_path,
    install_provisioner, mock_hosts
):
    pillar_new_key = 'test'

    # 1. prepare some valid pillar for the component
        # TODO python3.6 ???
    new_pillar_content = host.check_output(
        'python3.6 {0}/configure-eos.py {1} --show-{1}-file-format'.format(
            h.PRVSNR_REPO_INSTALL_DIR / 'cli' / 'utils', component
        )
    )
    new_pillar_dict = yaml.safe_load(new_pillar_content.strip())
    new_pillar_dict.update({pillar_new_key: "temporary"})

    component_pillar = '{}.sls'.format(component)
    tmp_file = tmp_path / component_pillar
    tmp_file.write_text(
        yaml.dump(new_pillar_dict, default_flow_style=False, canonical=False)
    )
    if not remote:
        host_tmp_file = host_tmpdir / component_pillar
        localhost.check_output(
            "scp -F {0} {1} {2}:{3}".format(
                ssh_config,
                tmp_file,
                hostname,
                host_tmp_file
            )
        )
        tmp_file = host_tmp_file

    # 2. call the update script
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO
        # TODO imporove
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        eos_pillar_update {} {} {} {} {}
    """.format(component, tmp_file, hostspec, ssh_config, with_sudo)

    res = run_script(
        script, host=(localhost if remote else host), script_path=script_path
    )

    # 3. verify
    assert res.rc == 0

    tmp_file_content = (localhost if remote else host).check_output('cat {}'.format(tmp_file))
    current_pillar = h.PRVSNR_REPO_INSTALL_DIR / 'pillar' / 'components' / component_pillar
    pillar_file_content = host.check_output('cat {}'.format(current_pillar))

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
        eos_pillar_load_default {} {} {} {}
    """.format(component, hostspec, ssh_config, with_sudo)

    res = run_script(
        script, host=(localhost if remote else host), script_path=script_path
    )

    # 5. verify
    assert res.rc == 0

    pillar_file_content = host.check_output('cat {}'.format(current_pillar))
    pillar_file_dict = yaml.safe_load(pillar_file_content)
    del new_pillar_dict[pillar_new_key]
    assert new_pillar_dict == pillar_file_dict

    assert res.stdout.count('SALT-ARGS: ') == len(expected_lines)

    stdout_lines = res.stdout.split(os.linesep)
    ind = stdout_lines.index(expected_lines[0])
    assert stdout_lines[ind:(ind + len(expected_lines))] == expected_lines
