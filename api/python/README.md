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

### From yum repository

Coming soon.


## Python API for NTP update

### ntp.py
Defines a python API to update NTP using below functions:
- update_pillar: 
    - Updates pillar data defined in /opt/seagate/eos-prvsnr/pillar/components/system.sls using Pillar class.
- refresh_ntpd: 
    - Restarts the ntpd service once the configuration file is updated.

### pillar.py
Defines pillar class to update the pillar data as per user inputs using below functions:
- __load_defaults:
    - Parse the default pillar document in a stream
- __backup_pillar:
    - Backup existing pillar document
- __save:
    - Updates the pillar document as per user input 

### How to use:
1. Set sys path to import python modules in different directories
    ```
    export PYTHONPATH=${PYTHONPATH}:/opt/seagate/eos-prvsnr/api/python/ 
    ```
2. Import any module from utils:
    ```
     from utils import pillar
    ```
3.  How to use:
    ```
    python3 ntp.py

    OR

    pyhton3 ntp.py '{ "time_server": "TIME-SERVER-IP", "timezone": "TIMEZONE" }'
    ```
