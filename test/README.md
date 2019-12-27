# Integration Tests

The test framework is intended to leverage the development process:
- provide fast feedback regarding proposed changes
- increase confidence in the code base
- prepare a solid base for CI

It is based on [pytest](http://doc.pytest.org/en/latest/contents.html) and [testinfra](https://testinfra.readthedocs.io/en/latest/index.html). Also it is highly recommended to use [flake8](http://flake8.pycqa.org/en/latest/) for static checks.


## Installation

- create and activate a python3 virtual environment for (e.g. using [virtualenv](https://virtualenv.pypa.io/en/latest/), [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) or [pipenv](https://pipenv-fork.readthedocs.io/en/latest/))
- `pip install -r test-requirements.txt`

## Run Static Linter

- `flake8 test`

## Run tests

- `pytest -l -v test`

### Useful Options

- `pytest ... test/<path-to-some-test-module>` to run tests only for some test module
- `-k pattern` to filter test by name, parameters etc.
- `-n auto` to run multiple tests processes in parallel using available CPU cores (check [pytest-xdist](https://docs.pytest.org/en/3.0.1/xdist.html))
- `--log-cli-level <LOG-LEVEL>` to pass logs to stdout/stderr

Please check `pytest --help` and [pytest docs](http://doc.pytest.org/en/latest/usage.html) for more info.

### Custom Options

- `--env-provider`: test environment provider, possible values: `host`, `docker`, `vagrant`, default: `docker`

*Note*. `host` and `vagrant` options are not actually ready to use for now.

Check `custom options` section of `pytest --help` for more information.


### Custom Markers

- `--env_name`: mark test to be run in the specific environment, default: `centos7-base`
- `--isolated`: mark test to be run in isolated environment instead of module wide shared, default: not set
- `--eos_spec`: mark test as expecting specific EOS stack configuration, default: not set
- `--hosts`: mark test as expecting the specified list of hosts, default: ['host']
- `--inject_repo`: mark test as expecting repo injection only for specified hosts, default: all hosts
- `--inject_ssh_config`: mark test as expecting ssh configuration only for specified hosts, default: all hosts
- `--mock_cmds`: mark test as requiring mocked system commands, default: not set

Check `pytest --markers` for more information.

## Test API

Test framework has helper.py and conftest.py which declare and implement the API&#39;s that can be used in tests. helper.py provides a set of helper functions and conftest.py provides a set of pytest fixtures that are accessible across multiple test files.

### helper.py

#### PRVSNR_REPO_INSTALL_DIR:
- Defines the path to the EOS provisioner installation directory

#### HostMeta:
- HostMeta class defines the host system with the attributes like,
  - **remote**: Remote host instance
  - **host**: Testinfra host instance
  - **ssh_config**: ssh_configurations of the host
  - **machine_name**: Remote hostname
  - **hostname**: Testinfra host instance hostname
  - **iface**: Interface of host

#### safe_filename:
- Sanitizes strings that are intended to be used as names of files/directories.
- Parameters:
  - **name** - is a string to sanitize
- Returns: sanitized string

#### mock_system_cmd:
- Mocks `cmd` on a `host` in such a way that command arguments are printed to standard output with prefix "`<CMD>-ARGS`: ", where `<CMD>` is uppercase for `cmd`.
- Parameters:
  - **host** - testinfra&#39;s host instance
  - **cmd** - command to mock on a host
  - **bin_path** - bin path (default: /usr/local/bin)

#### restore_system_cmd:
- Reverses the [mock_system_cmd](#mock_system_cmd)
- Parameters:
  - **host** - testinfra&#39;s host instance
  - **cmd** - command to mock on a host
  - **bin_path** - bin path (default: /usr/local/bin)

#### run:
- Executes the provided input script on the host and optionally dumps stdout and stderr to logs. Wraps [testinfra API](https://testinfra.readthedocs.io/en/latest/modules.html#testinfra.host.Host.run). If the command fails or `force_dump` is set to `True` it logs stdout with level DEBUG and stderr with level ERROR.
- Parameters:
  - **host** - testinfra&#39;s host instance
  - **script** - script to execute on host
  - **force_dump** - dump stderr and stdout in any case  (default: false)
-  Returns: result of script execution

#### check_output:
- Executes the input script on the host using [run](#run) method and asserts the result is 0. Wraps [testinfra API](https://testinfra.readthedocs.io/en/latest/modules.html#testinfra.host.Host.check_output). And optionally dumps stdout and stderr to logs.
- Parameters:
  - **host** - testinfra&#39;s host instance
  - **script** - script to execute on host
- Returns: standard output of script execution

#### inject_repo:
- Copies repository data on the hosts in the provided host_repo_dir path.
- Parameters:
  - **localhost** - localhost instance from fixture
  - **host** - host instance
  - **ssh_config** - path to ssh_config from fixture
  - **project_path** - path of local ees-prvsnr repository from fixture
  - **host_repo_dir** - path to copy ees-prvsnr
- Returns: path of copied repository on the `host`

### conftest.py

#### project_path:
- Returns the full path of local ees-prvsnr repository.
- Scope: `session`

#### localhost:
- Returns testinfra&#39;s host object for the localhost.
- Scope:  `session`

#### tmpdir_session:
- Returns a session-scoped base temporary directory
- Scope: `session`

#### tmpdir_module:
- Returns a module-scoped base temporary directory.
- Scope: `module`

#### tmpdir_function:
- Returns function-scoped base temporary directory
- Scope: `function`

#### ssh_config:
- Returns path of ssh_config file
- Scope: `function`

#### ssh_key:
- Returns ssh\_key file to access remote hosts
- Scope: `function`

#### rpm_prvsnr:
- Builds provisioner rpm inside dynamically provisioned remote and returns path to the rpm on a localhost.
- Scope: `session`

#### env_name:
- Returns a pair `<os>-<env>` of targeted base operating system and environment level.
- Scope: `module`

#### post_host_run_hook:
-  Returns a callback which should be called once the host is started.
- Scope: `module`

#### hosts:
- Returns a dictionary of the hosts provided for the test. Key is host label, value is testinfra&#39;s host instance.
- Scope: `function`

#### mock_hosts:
- Mocks system commands on hosts specified by `mock_cmds` marker.
- Scope: `function`

#### inject_ssh_config:
- Adds the ssh_config to host instances
- Scope: `function`

#### eos_spec:
- Returns a dictionary of the specific EOS stack configuration.
- Returned eos_spec dictionary will be a nested dictionary with the host_eosnode1, host_eosbode2, etc. dictionaries
- host_eosnode1 and host_eosnode2 has
    - key: minion_id and value: salt minion id of EOS node
    - key: is_primary and value: true/false
- Scope: `function`

#### eos_hosts:
- Returns a dictionary of EOS host nodes
- Returned eos_hosts dictionary has
    - key: host and value: host instance
    - key: minion_id and value: salt minion id 
    - key: is_primary and value: true/false
- Scope: `function`

#### eos_primary_host:
- Returns primary EOS node instance
- Scope: `function`

#### eos_primary_host_label:
- Returns host fixture label of a primary EOS node
- Scope: `function`

#### eos_primary_host_ip:
- Returns primary EOS host ip address
- Scope: `function`

#### configure_salt:
- configures the salt on EOS nodes.
- Scope: `function`

#### accept_salt_keys:
- Accepts the salt keys from minions on a primary EOS node
- Scope: `function`


## To add new tests (In progress)

1. For any new functionality, add fixture or helper function inside the conftest.py and helper.py. Reuse the fixtures and helper functions if applicable.
2. Import fixtures in the test file if using.
3. Add tests file according to the functionality. E.g, For component related tests, add/update srv/components/ tests.



## Test Environment Providers

For better tests isolation they are run inside virtual environments powered by `docker` and `vagrant` (not actually ready yet).

Host based testing is possible as well (not actually ready yet) but it leads to worse tests isolation and requires more accurate setup/teardown routine. Not all tests can satisfy that.

### Docker

Docker images can be found in [images](../images/docker).
They are built automatically at tests setup phase.
Docker containers are created during the tests setup phase as well and removed during the teardown phase.

### Vagrant

*TODO*

### Host Based

*TODO*
