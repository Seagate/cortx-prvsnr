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

- `--envprovider`: test environment provider, possible values: `host`, `docker`, `vagrant`, default: `docker`

*Note*. `host` and `vagrant` options are not actually ready to use for now.

Check `custom options` section of `pytest --help` for more information.


### Custom Markers

- `--env_name`: mark test to be run in the specific environment, default: `centos7-base`
- `--isolated`: mark test to be run in isolated environment instead of module wide shared, default: not set

Check `pytest --markers` for more information.

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
