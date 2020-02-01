# Provisioner API

This is a northbound interface for EOS components that provides API
to configure provisioned EOS stack.

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

The API is now bundled as part of provisioner rpm package `eos-prvsnr`.

During the installation the api package is placed in `/opt/seagate/eos-prvsnr/api/python` directory.

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
