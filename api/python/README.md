# Provisioner API

This is a northbound interface for EOS components that provides API
to configure provisioned EOS stack.

It uses saltstack client python API and should be called on the same machine where
salt master is running.

## Requirements

1. Should be called on the same machine where salt master is running
2. Exteranl auth for salt should be respected `TODO`


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


## Authentication Initialization

To be used by non-root user the API requires additional initialization:

```
from provisioner.salt import auth_init

auth_init(username=username, password=password)
```

where `username` is a name of the user that is added to `prvsnrusers` group.
So you should either add and existent user to that group or create new one and
pass his name along with his password to `auth_init`.

## API

*TODO*

## Usage examples

### NTP configuration

```
    from provisioner.errors import ProvisionerError
    from provisioner import get_params, set_ntp

    # get current values

    try:
        curr_params = get_params('ntp_server', 'ntp_timezone')
    except ProvisionerError:
        raise

    api_ntp_server = curr_params['ntp_server']
    api_ntp_timezone = curr_params['ntp_timezone']

    # set new ones

    new_ntp_server = '0.north-america.pool.ntp.org'
    new_ntp_timezone = 'Europe/Berlin'

    try:
        set_ntp(server=new_ntp_server, timezone=new_ntp_timezone)
    except ProvisionerError:
        raise
```
