import os
import pytest
import json
from pathlib import Path

import logging
import testinfra

from test.helper import PRVSNR_REPO_INSTALL_DIR

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
def host_ssh_config(host, host_tmp_path):
    fpath = host_tmp_path / 'ssh_config'
    host.check_output("touch {}".format(fpath))
    return fpath


@pytest.fixture
def run_script(localhost, tmp_path, ssh_config, request):

    def _f(test_content, trace=False, host=None, host_tmp_path=None, script_path=DEFAULT_SCRIPT_PATH):
        host = request.getfixturevalue('host') if host is None else host
        host_tmp_path = request.getfixturevalue('host_tmp_path') if host_tmp_path is None else host_tmp_path
        hostname = host.check_output('hostname')

        test_script_name = 'test_script.sh'
        test_script_path = tmp_path / test_script_name
        test_script_path.write_text("set -e\n. {}\n{}".format(script_path, test_content))

        if host is not localhost:
            host_script_path = host_tmp_path / test_script_name
            localhost.check_output(
                "scp -F {0} {1} {2}:{3}".format(
                    ssh_config,
                    test_script_path,
                    hostname,
                    host_script_path
                )
            )
            test_script_path = host_script_path

        res = None
        try:
            res = host.run(
                "bash {} {} 2>&1"
                .format(
                    '-x' if trace else '',
                    test_script_path
                )
            )
        finally:
            if res is not None:
                for line in res.stdout.split(os.linesep):
                    logger.debug(line)

        return res

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
                {}
            """.format(
                before_script,
                add_opts,
                add_long_opts,
                opts_cb,
                positional_args_cb,
                ' '.join([*args]),
                (
                    "echo \"Parsed args: dry-run=<$dry_run>, remote=<$hostspec>, "
                    "singlenode=<$singlenode>, ssh-config=<$ssh_config>, sudo=<$sudo>, "
                    "verbosity=<$verbosity>\""
                ),
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
    res = parse_args()
    assert res.rc == 0
    assert "dry-run=<false>" in res.stdout
    assert "remote=<>" in res.stdout
    assert "singlenode=<false>" in res.stdout
    assert "ssh-config=<>" in res.stdout
    assert "sudo=<false>" in res.stdout


def test_functions_parse_args_parses_dry_run(parse_args):
    for arg in ('-n', '--dry-run'):
        res = parse_args(arg)
        assert res.rc == 0
        assert "dry-run=<true>" in res.stdout


def test_functions_parse_args_parses_singlenode(parse_args):
    for arg in ('-S', '--singlenode'):
        res = parse_args(arg)
        assert res.rc == 0
        assert "singlenode=<true>" in res.stdout


def test_functions_parse_args_parses_remote(parse_args):
    hostspec = 'user@host'
    for arg in ('-r', '--remote'):
        res = parse_args(arg, hostspec)
        assert res.rc == 0
        assert "remote=<{}>".format(hostspec) in res.stdout


def test_functions_parse_args_parses_ssh_config(parse_args, host_ssh_config):
    for arg in ('-F', '--ssh-config'):
        res = parse_args(arg, str(host_ssh_config))
        assert res.rc == 0
        assert "ssh-config=<{}>".format(host_ssh_config) in res.stdout


def test_functions_parse_args_parses_sudo(parse_args):
    for arg in ('-s', '--sudo'):
        res = parse_args(arg)
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
        '-n,  --dry-run',
        '-h,  --help',
        '-r,  --remote [user@]hostname',
        '-S,  --singlenode',
        '-F,  --ssh-config FILE',
        '-s,  --sudo',
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


def test_functions_check_host_in_ssh_config(run_script, host, host_tmp_path):
    host_ssh_config = host_tmp_path / 'ssh-config'
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
            assert host.file(str(PRVSNR_REPO_INSTALL_DIR / path)).exists


# TODO remote case is better to test from within virtual env as well
@pytest.mark.isolated
@pytest.mark.env_name('centos7-utils')
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_install_provisioner_local(
    run_script, host, hostname, localhost,
    ssh_config, remote, project_path,
    request
):
    host_project_path = None
    if remote is True:
        script_path = project_path / 'cli' / 'src' / 'functions.sh'
    else:
        host_project_path = request.getfixturevalue('inject_repo')['host']
        script_path = host_project_path / 'cli/src/functions.sh'

    prvsnr_version = 'ees1.0.0-PI.2-sprint7'
    hostspec = hostname if remote else "''"
    ssh_config = ssh_config if remote else "''"
    with_sudo = 'false' # TODO

    script = """
        install_provisioner local {} {} {} {}
    """.format(prvsnr_version, hostspec, ssh_config, with_sudo)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)

    assert res.rc == 0

    # TODO some more strict checks
    # check repo files are in place
    for path in ('files', 'pillar', 'srv', 'cli'):
        assert host.file(str(PRVSNR_REPO_INSTALL_DIR / path)).exists

    if remote is True:
        assert not localhost.file(str(project_path / 'repo.zip')).exists
        assert not host.file('/tmp/repo.zip').exists
    else:
        assert not host.file(str(host_project_path / 'repo.zip')).exists



@pytest.mark.isolated
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
    ssh_config, remote, project_path,
    install_provisioner
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
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize("master", [True, False], ids=['master', 'minion'])
def test_functions_configure_salt(
    run_script, host, hostname, localhost,
    ssh_config, remote, master, project_path,
    install_provisioner
):
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

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0

    host.check_output(
        'diff -q {} /etc/salt/master'.format(
            PRVSNR_REPO_INSTALL_DIR / 'files/etc/salt/master'
        )
    )
    host.check_output(
        'diff -q {} /etc/salt/minion'.format(
            PRVSNR_REPO_INSTALL_DIR / 'files/etc/salt/minion'
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
        accept_salt_keys {} {} {} {} 10
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
        accept_salt_keys {} {} {} {} 10
    """.format(minion_id, hostspec, ssh_config, with_sudo)

    res = run_script(script, host=(localhost if remote else host), script_path=script_path)
    assert res.rc == 0
    assert (
        "WARNING: no key acceptance is needed for minion {}"
        .format(minion_id) in res.stdout
    )



@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.hosts(['host_eosnode1', 'host_eosnode2'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
def test_functions_accept_salt_keys_cluster(
    run_script, host_eosnode1, host_eosnode2, hostname_eosnode1,
    host_tmp_path_eosnode1, host_tmp_path_eosnode2,
    localhost, ssh_config, remote, project_path,
    install_provisioner
):
    eosnode1_minion_id = 'eosnode-1'
    eosnode2_minion_id = 'eosnode-2'
    with_sudo = 'false' # TODO

    salt_server_ip = host_eosnode1.interface("eth0").addresses[0]

    # configure eosnode-1
    script = """
        configure_salt {} '' '' {} true localhost
    """.format(
        eosnode1_minion_id, with_sudo, salt_server_ip
    )
    res = run_script(script, host=host_eosnode1, host_tmp_path=host_tmp_path_eosnode1)
    assert res.rc == 0

    # configure eosnode-2
    script = """
        configure_salt {} '' '' {} false {}
    """.format(
        eosnode2_minion_id, with_sudo, salt_server_ip
    )
    res = run_script(script, host=host_eosnode2, host_tmp_path=host_tmp_path_eosnode2)
    assert res.rc == 0

    hostspec = hostname_eosnode1 if remote else "''"
    ssh_config = ssh_config if remote else "''"
    # TODO improve
    script_path = (project_path / 'cli' / 'src' / 'functions.sh') if remote else DEFAULT_SCRIPT_PATH

    script = """
        accept_salt_keys "{} {}" {} {} {} 10
    """.format(eosnode1_minion_id, eosnode2_minion_id, hostspec, ssh_config, with_sudo)

    res = run_script(
        script, host=(localhost if remote else host_eosnode1),
        host_tmp_path=host_tmp_path_eosnode1,
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
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "component",
    ['cluster', 'eoscore', 'haproxy', 'release', 's3client', 's3server', 'sspl']
)
def test_functions_eos_pillar_show_skeleton(
    run_script, host, hostname, host_tmp_path,
    localhost, tmp_path,
    ssh_config, remote, component, project_path,
    install_provisioner
):
    # 1. get pillar to compare
    # TODO python3.6 ???
    pillar_content = host.check_output(
        'python3.6 {0}/configure-eos.py {1} --show-{1}-file-format'.format(
            PRVSNR_REPO_INSTALL_DIR / 'cli' / 'utils', component
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
def test_functions_eos_pillar_update_fail(
    run_script, host, ssh_config, install_provisioner
):
    res = run_script('eos_pillar_update cluster some-path', host=host)
    assert res.rc == 1
    assert 'ERROR: not a file' in res.stdout


# TODO
#   - might need to improve ???
#   - 'centos7-salt-installed' is used since it has python3.6 installed,
#      python and repo installed would be enough actually
#   - do we need to test all components actually, might be a subject of other test
#     (e.g. for utils)
@pytest.mark.isolated
@pytest.mark.env_name('centos7-salt-installed')
@pytest.mark.mock_cmds(['salt'])
@pytest.mark.parametrize("remote", [True, False], ids=['remote', 'local'])
@pytest.mark.parametrize(
    "component",
    ['cluster', 'eoscore', 'haproxy', 'release', 's3client', 's3server', 'sspl']
)
def test_functions_eos_pillar_update(
    run_script, host, hostname, host_tmp_path,
    localhost, tmp_path,
    ssh_config, remote, component, project_path,
    install_provisioner, mock_hosts
):
    # 1. prepare some valid pillar for the component
    component_pillar = '{}.sls'.format(component)
        # TODO python3.6 ???
    new_pillar_content = host.check_output(
        'python3.6 {0}/configure-eos.py {1} --show-{1}-file-format'.format(
            PRVSNR_REPO_INSTALL_DIR / 'cli' / 'utils', component
        )
    )
    tmp_file = tmp_path / component_pillar

        # TODO might need to update configure-eos.py to dump with endline at end
    tmp_file.write_text(new_pillar_content + '\n')
    if not remote:
        host_tmp_file = host_tmp_path / component_pillar
        localhost.check_output(
            "scp -F {0} {1} {2}:{3}".format(
                ssh_config,
                tmp_file,
                hostname,
                host_tmp_file
            )
        )
        tmp_file = host_tmp_file

    # 2. remove original pillar to ensure that coming update is applied
        # TODO better to have modified pillar
    original_pillar = PRVSNR_REPO_INSTALL_DIR / 'pillar' / 'components' / component_pillar
    host.check_output('rm -f {}'.format(original_pillar))

    # 3. call the script
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

    # 4. verify
    assert res.rc == 0

    # TODO check md5sum is everywhere available
    tmp_file_hash = (localhost if remote else host).check_output('md5sum {}'.format(tmp_file))
    pillar_file_hash = host.check_output('md5sum {}'.format(original_pillar))
    assert tmp_file_hash.split()[0] == pillar_file_hash.split()[0]

    # check that pillar has been refreshed on the minions
    expected_lines = [
        'SALT-ARGS: * saltutil.refresh_pillar'
    ]
    assert res.stdout.count('SALT-ARGS: ') == len(expected_lines)

    stdout_lines = res.stdout.split(os.linesep)
    ind = stdout_lines.index(expected_lines[0])
    assert stdout_lines[ind:(ind + len(expected_lines))] == expected_lines
