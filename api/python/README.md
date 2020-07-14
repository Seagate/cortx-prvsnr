# Provisioner API

This is a northbound interface for CORTX components that provides API
to configure provisioned software stack.

It uses saltstack client python API and should be called on the same machine where
salt master is running.


There are set of api levels:
1. [base python api](#api) that communicates directly with underlying salt api
2. provisioner [cli tool](#cli)
3. python api that uses provisioner cli and acts as a thin alternative for base one


The one may choose an api depending it their needs:
* base python api is the best choice for python libraries and apps since
  it can be utilized in usual way
* python api over cli might be the better for python apps that are going
  to be frozen since it doesn't have other python dependencies than system ones
* cli is to be consumed by any non-python app & library as usual shell tool


## Requirements

1. Should be called on the same machine where salt master is running
2. External auth for salt should be [respected](#authentication_initialization)


## Installation

### From GitLab

```
    pip install  git+http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr#subdirectory=api/python
```

Will install `master` branch version.
To install specific `version` (it might be any branch, tag or commit sha1):

```
    pip install  git+http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr@version#subdirectory=api/python
```

SSH based installation is also possible, e.g.

```
    pip install git+ssh://git@gitlab.mero.colo.seagate.com:6022/eos/provisioner/ees-prvsnr.git#subdirectory=api/python
```

### From yum repository

The API is now bundled as part of provisioner rpm package `cortx-prvsnr`.

During the installation the api package is placed in `/opt/seagate/cortx/provisioner/api/python` directory.

Also it is installed to global python3 environment and available for usual python imports.


## Configuration


### Switching Python API

By default base Provisioner Python API is enabled. To switch to Python CLI wrapper:


```
import provisioner

provisioner.set_api('pycli')
```


### Authentication Initialization

To be used by non-root user the API requires additional initialization:

```
import provisioner

provisioner.auth_init(username=username, password=password)
```

where `username` is a name of the user that is added to `prvsnrusers` group.
So you should either add and existent user to that group or create new one and
pass his name along with his password to `auth_init`.

## API

*TODO*

## Output

Supported output formats:
  - plain
  - json
  - yaml

Might be configured using (from lower to higher precedence):
  - environment variable `PRVSNR_OUTPUT`, defaults to `plain`
  - cli tool option `--output`, defaults to `PRVSNR_OUTPUT` env variable value

## Logging

Supported logging handlers (might be combined):
- `console`: logs to either `stdout` or `stderr`
- `rsyslog`: logs to rsyslog
- `logfile`: logs to specified file with log rotation

Supported logging formats:
- `human` human friendly format oriented on progress output
- `full` rich logging format with many fields good for logs exploration and debugging

Ways of configuration:
- configuration file (from lower to higher precedence):
    - hardcoded logging configuration
    - `<api package installation directory>/provisioner.conf`
- cli tool options (overides configuration file options):
    - common for all handlers:
        - `--<handler>` - enables a `<handler>`
        - `--no<handler>` - disables a `<handler>`
        - `--<handler>-level {DEBUG|INFO|WARN|ERROR}` - sets logging level for a `<handler>`
        - `--<handler>-formatter {human|full}` - sets logging format for a `<handler>`
    - specific:
        - `--console-stream {stderr|stdout}`
        - `--logfile-filename <path>` path to a log file
        - `--logfile-maxBytes <bytes>` max file size in bytes
        - `--logfile-backupCount <number>` max backup log files number

### Default settings

Provisioner confiuration file:
- `console` handler:
    - enabled
    - log format is `human`
    - log level is `INFO`
    - log stream is `stderr`
- `rsyslog` handler:
    - enabled
    - log format is `full`
    - log level is `DEBUG`
- `logfile` handler:
    - disabled
    - log format is `full`
    - log level is `DEBUG`
    - `filename` is `./prvsnr-api.log`
    - `maxBytes` is `10485760` (`10 MB`)
    - `backupCount` is `10`

Hardcoded configuration (used if no configuation file is found):
- `console` handler is enabled with `full` format and `DEBUG` level

### Additional CLI logging rules

1. if `output` is set to machine readable one (`json`, `yaml`) then `console`
   handler is disabled
2. if api command is one of `LOG_FORCED_LOGFILE_CMDS` in [config.py](provisioner/config.py) then:
    - `logfile` handler is enabled
    - if no value for `filename` is provided then it is generated. Genarated
      files are located in either `/var/log/seagate/provisioner` or in the current
      directory if the former doesn't exist.


## Usage examples

### Integration with apps going to be frozen

Please use python api over cli if you use some python freezer to distribute
your application (e.g. [pyinstaller](https://www.pyinstaller.org/)).

There is a helper module `provisioner.freeze` that you might want to import
to make the integration easier:

```
    import provisioner
    import provisioner.freeze

    pillar = provisioner.pillar_get()
    ...
```


### NTP configuration

```
    from provisioner import get_params, set_ntp

    # get current values
    curr_params = get_params('ntp_server', 'ntp_timezone')

    api_ntp_server = curr_params['ntp_server']
    api_ntp_timezone = curr_params['ntp_timezone']

    # set new ones
    new_ntp_server = '0.north-america.pool.ntp.org'
    new_ntp_timezone = 'Europe/Berlin'

    set_ntp(server=new_ntp_server, timezone=new_ntp_timezone)
```

## CLI

Provisioner provides CLI tool `provisioner` that allows one to interact with system configuration manager
via shell.

### CLI Installation

The tool `provisioner` becomes available once the provisioner api module is [installed](#installation)
in your system or python virtual environtment.

### CLI Usage

CLI wraps provisioner api. Please refer to its usage help `provisioner --help` for more details.

#### Passing crdedentials to CLI

To pass authnetication for non-root users you will likely need to provider credentials to CLI.
There are multiple options how to do that:
1. using stdin: `echo <password> | provisioner --username <username> --password -`
2. as env variable `PRVSNR_PASSWORD`: `PRVSNR_PASSWORD=<password> provisioner --username <username>`
3. (insecure) as command line argument: `provisioner --username <username> --password <password>`

# Development

## docstrings

Pattern:

```
    """<title>

    :param <name>: [(optional)] <descr>
    [:type <name>: <types>]
    :return: <descr>
    [:rtype: <type>]

    [
    Usage::

      >>> <python expressions>
      <output>
    ]
    """
```
