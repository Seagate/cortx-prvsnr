# Introduction

# Integration Tests

**Table of Contents**

- [Integration Tests](#integration-tests)
  - [Introduction](#introduction)
  - [Installation](#installation)
  - [Run Static Linter](#run-static-linter)
  - [Run tests](#run-tests)
    - [Run unit tests only](#run-unit-tests-only)
    - [Useful Options](#useful-options)
    - [Custom Options](#custom-options)
    - [Custom Markers](#custom-markers)
  - [Test API](#test-api)
    - [`helper.py`](#helperpy)
      - [`PRVSNR_REPO_INSTALL_DIR`](#prvsnr_repo_install_dir)
      - [`HostMeta`](#hostmeta)
      - [`safe_filename`](#safe_filename)
      - [`mock_system_cmd`](#mock_system_cmd)
      - [`restore_system_cmd`](#restore_system_cmd)
      - [`run`](#run)
      - [`check_output`](#check_output)
      - [`inject_repo`](#inject_repo)
    - [`conftest.py`](#conftestpy)
      - [`project_path`](#project_path)
      - [`localhost`](#localhost)
      - [`tmpdir_session`](#tmpdir_session)
      - [`tmpdir_module`](#tmpdir_module)
      - [`tmpdir_function`](#tmpdir_function)
      - [`ssh_config`](#ssh_config)
      - [`ssh_key`](#ssh_key)
      - [`rpm_prvsnr`](#rpm_prvsnr)
      - [`env_level`](#env_level)
      - [`post_host_run_hook`](#post_host_run_hook)
      - [`hosts`](#hosts)
      - [`mock_hosts`](#mock_hosts)
      - [`inject_ssh_config`](#inject_ssh_config)
      - [`cortx_spec`](#cortx_spec)
      - [`cortx_hosts`](#cortx_hosts)
      - [`cortx_primary_host`](#cortx_primary_host)
      - [`cortx_primary_host_label`](#cortx_primary_host_label)
      - [`cortx_primary_host_ip`](#cortx_primary_host_ip)
      - [`configure_salt`](#configure_salt)
      - [`accept_salt_keys`](#accept_salt_keys)
  - [To add new tests (In progress)](#to-add-new-tests-in-progress)
  - [Test Environment Providers](#test-environment-providers)
    - [Docker](#docker)
    - [Vagrant](#vagrant)
    - [Host Based](#host-based)


## Introduction

The test framework is intended to leverage the development process:

- provide fast feedback regarding proposed changes
- increase confidence in the code base
- prepare a solid base for CI

It is based on [`pytest`][pytest] and [`testinfra`][testinfra]. Also it is highly
recommended to use [`flake8`][flake8] for static checks.

[pytest]: http://doc.pytest.org/en/latest/contents.html
[testinfra]: https://testinfra.readthedocs.io/en/latest/index.html
[flake8]: http://flake8.pycqa.org/en/latest/


# Installation

Please refer the [doc](../docs/testing.md#python-environment-preparation).


# Runnning

## Static Linter

```bash
flake8 test
```

## Functional testing

```bash
pytest -l -v
```

### Unit tests

There is a subset of tests that verifies some scoped logic in a way
of [unit testing](https://en.wikipedia.org/wiki/Unit_testing).

These tests are:

- safe to run on a local host since they don't require any virtual environment
- fast, usually will end in a minute or less

To filter that tests `unit` marker is available:

- `pytest -m unit --collect-only` will show all unit tests available
- `pytest -m unit` will run the tests

To mark a test as a unit you may:

- use the `unit` marker
- use the `unit` fixture (a good way to mark a bunch of tests)


### Useful Options

- `pytest ... test/<path-to-some-test-module>` to run tests only for some test
  module
- `-k pattern` to filter test by name, parameters etc.
- `-m expr` to filter tests by marker
- `-n auto` to run multiple tests processes in parallel using available CPU
  cores (check [`pytest-xdist`](https://docs.pytest.org/en/3.0.1/xdist.html))
- `--log-cli-level <LOG-LEVEL>` to pass logs to `stdout`/`stderr`

Please check `pytest --help` and
[`pytest` docs](http://doc.pytest.org/en/latest/usage.html) for more info.

### Custom Options

- `--env-provider`: test environment provider, possible values: `host`,
  `docker`, `vagrant`, default: `docker`

*Note*. `host` and `vagrant` options are not actually ready to use for now.

Check `custom options` section of `pytest --help` for more information.


### Custom Markers

- `--env_level`: mark test to be run in the specific environment level, default:
  `base`
- `--isolated`: mark test to be run in isolated environment instead of module
  wide shared, default: not set
- `--cortx_spec`: mark test as expecting specific CORTX stack configuration,
  default: not set
- `--hosts`: mark test as expecting the specified list of hosts, default:
  ['host']
- `--inject_repo`: mark test as expecting repo injection only for specified
  hosts, default: all hosts
- `--inject_ssh_config`: mark test as expecting SSH configuration only for
  specified hosts, default: all hosts
- `--mock_cmds`: mark test as requiring mocked system commands, default: not set

Check `pytest --markers` for more information.


# Test API

Test framework has [helper.py][helper.py] and [conftest.py][conftest.py] which declare
and implement the Cortx Provisioner testing framework API. It can be used in tests 
for the common routine () and simplifies tests development allowing to focus mostly
on a test scenarion instead of some infra management routine.

[helper.py]: helper.py
[conftest.py]: conftest.py


[helper.py][helper.py] provides a set of helper functions and [conftest.py][conftest.py]
provides a set of pytest fixtures that are accessible across multiple test modules.

## Tips & Tricks

### How to mark test as a Unit

Option 1: use `unit` marker

```python
@pytest.mark.unit
def test_something():
    ...
```

Option 2: use `unit` fixture

```python
# for a test
def test_something(unit):
    ...

# for all tests in a module
# somemodule.py
@pytest.fixture(scope='session', autouse=True)
def unit():
    ...

# for all tests in multiple modules
# conftest.py
@pytest.fixture(scope='session', autouse=True)
def unit():
    ...
```



### `helper.py`


#### `PRVSNR_REPO_INSTALL_DIR`

- Defines the path to the CORTX provisioner installation directory


#### `HostMeta`

- HostMeta class defines the host system with the attributes like:
  - `remote`: Remote host instance
  - `host`: Testinfra host instance
  - `ssh_config`: `ssh_configurations` of the host
  - `machine_name`: Remote hostname
  - `hostname`: Testinfra host instance hostname
  - `interface`: Interface of host


#### `safe_filename`

- Sanitizes strings that are intended to be used as names of files/directories.
- Parameters:
  - `name` - is a string to sanitize
- Returns: sanitized string


#### `mock_system_cmd`

- Mocks `cmd` on a `host` in such a way that command arguments are printed to
  standard output with prefix "`<CMD>-ARGS`: ", where `<CMD>` is uppercase for
  `cmd`.
- Parameters:
  - `host` - testinfra's host instance
  - `cmd` - command to mock on a host
  - `bin_path` - bin path (default: `/usr/local/bin`)


#### `restore_system_cmd`

- Reverses the [`mock_system_cmd`](#mock_system_cmd)
- Parameters:
  - `host` - testinfra's host instance
  - `cmd` - command to mock on a host
  - `bin_path` - bin path (default: `/usr/local/bin`)


#### `run`

- Executes the provided input script on the host and optionally dumps `stdout`
  and `stderr` to logs. Wraps [testinfra API][testinfra-API]. If the command
  fails or `force_dump` is set to `True` it logs `stdout` with level `DEBUG` and
  `stderr` with level `ERROR`.
- Parameters:
  - `host` - testinfra's host instance
  - `script` - script to execute on host
  - `force_dump` - dump `stderr` and `stdout` in any case (default: false)
-  Returns: result of script execution

[testinfra-API]: https://testinfra.readthedocs.io/en/latest/modules.html#testinfra.host.Host.run


#### `check_output`

- Executes the input script on the host using [run](#run) method and asserts the
  result is 0. Wraps [testinfra API][testinfra-API]. And optionally dumps `stdout`
  and `stderr` to logs.
- Parameters:
  - `host` - testinfra's host instance
  - `script` - script to execute on host
- Returns: standard output of script execution


#### `inject_repo`

- Copies repository data on the hosts in the provided `host_repo_dir` path.
- Parameters:
  - `localhost` - localhost instance from fixture
  - `host` - host instance
  - `ssh_config` - path to `ssh_config` from fixture
  - `project_path` - path of local `ldr-r1-prvsnr` repository from fixture
  - `host_repo_dir` - path to copy `ldr-r1-prvsnr`
- Returns: path of copied repository on the `host`


### `conftest.py`

#### `project_path`

- Returns the full path of local `ldr-r1-prvsnr` repository.
- Scope: `session`


#### `localhost`

- Returns testinfra's host object for the localhost.
- Scope:  `session`


#### `tmpdir_session`

- Returns a session-scoped base temporary directory
- Scope: `session`


#### `tmpdir_module`

- Returns a module-scoped base temporary directory.
- Scope: `module`


#### `tmpdir_function`

- Returns function-scoped base temporary directory
- Scope: `function`


#### `ssh_config`

- Returns path of `ssh_config` file
- Scope: `function`


#### `ssh_key`

- Returns `ssh_key` file to access remote hosts
- Scope: `function`


#### `rpm_prvsnr`

- Builds provisioner rpm inside dynamically provisioned remote and returns path
  to the rpm on a localhost.
- Scope: `session`


#### `env_level`

- Returns a pair `<os>-<env>` of targeted base operating system and environment
  level.
- Scope: `module`

#### `post_host_run_hook`

- Returns a callback which should be called once the host is started.
- Scope: `module`


#### `hosts`

- Returns a dictionary of the hosts provided for the test. Key is host label,
  value is testinfra's host instance.
- Scope: `function`


#### `mock_hosts`

- Mocks system commands on hosts specified by `mock_cmds` marker.
- Scope: `function`


#### `inject_ssh_config`

- Adds the `ssh_config` to host instances
- Scope: `function`


#### `cortx_spec`

- Returns a dictionary of the specific CORTX stack configuration.
- Returned `cortx_spec` dictionary will be a nested dictionary with the
  `host_srvnode1`, `host_srvnode2`, etc. dictionaries
- `host_srvnode1` and `host_srvnode2` has
    - key: `minion_id` and value: salt minion id of CORTX node
    - key: `is_primary` and value: `true`/`false`
- Scope: `function`


#### `cortx_hosts`

- Returns a dictionary of CORTX host nodes
- Returned `cortx_hosts` dictionary has
    - key: `host` and value: host instance
    - key: `minion_id` and value: salt minion id
    - key: `is_primary` and value: `true`/`false`
- Scope: `function`


#### `cortx_primary_host`

- Returns primary CORTX node instance
- Scope: `function`


#### `cortx_primary_host_label`

- Returns host fixture label of a primary CORTX node
- Scope: `function`


#### `cortx_primary_host_ip`

- Returns primary CORTX host IP address
- Scope: `function`


#### `configure_salt`

- configures the salt on CORTX nodes.
- Scope: `function`


#### `accept_salt_keys`

- Accepts the salt keys from minions on a primary CORTX node
- Scope: `function`


## To add new tests (In progress)

1. For any new functionality, add fixture or helper function inside the
   `conftest.py` and `helper.py`. Reuse the fixtures and helper functions if
   applicable.
2. Import fixtures in the test file if using.
3. Add tests file according to the functionality. E.g, For component related
   tests, add/update `srv/components/` tests.


## Test Environment Providers

For better tests isolation they are run inside virtual environments powered by
`docker` and `vagrant` (not actually ready yet).

Host based testing is possible as well (not actually ready yet) but it leads to
worse tests isolation and requires more accurate setup/teardown routine. Not all
tests can satisfy that.


### Docker

Docker images can be found in [images](../images/docker). They are built
automatically at tests setup phase. Docker containers are created during the
tests setup phase as well and removed during the teardown phase.


### Vagrant

*TODO*

### Host Based

*TODO*
