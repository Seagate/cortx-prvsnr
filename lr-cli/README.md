# Cortx setup CLI

This is a northbound interface for CORTX components that provides CLI
to configure complete cortx software stack.

## Requirements

1. Salt-minion/master should be configured.
2. All cortx packages should be installed.
3. /etc/pip.conf should be in place to install this package. (refer [doc](https://seagate-systems.atlassian.net/wiki/spaces/PUB/pages/213549354/CORTX+Manual+Deployment+on+Single+Node+VM#Pre-requisite-steps))


## Installation

### From Github

to install specific `version` (it might be any branch):

```
    pip install  git+http://github.com/Seagate/cortx-prvsnr@main#subdirectory=lr-cli/
```

## CLI

## Architecture
We have design CLI framework which get inputs from user and update in confstore and pillar.
In field it apply network, firewall, ntp and storage changes to each node.
It is responsible to create cortx cluster as well.

1. main.py: This is entry point for cortx setup commands.
2. api_spec.yaml: This file include mapping of command with actual python class.
3. config.py: Include common configs of cortx setup commands.
4. setup.py: This file is used to bundle cortx_setup command and installed using pip.
5. logs.py: Handled logging for all commands & logs will be available on console and `/var/log/seagate/provisioner/nodecli.log`.
6. validate.py: common validation functions, for example: ipv4, hostnames etc.
7. commands: This folder contains actual implementation of commands.


## Usage examples
## CLI
CLI wraps cortx_setup CLI. Please refer to its usage help `cortx_setup --help` for more details


```
$ cortx_setup --help
usage: cortx_setup CLI  [-h]
                        {hostname,pillar_sync,salt_cleanup,server,network,node,cluster,resource,security,signature,storage,storageset,enclosure,prepare_confstore}
                        ...

positional arguments:
  {hostname,pillar_sync,salt_cleanup,server,network,node,cluster,resource,security,signature,storage,storageset,enclosure,prepare_confstore}

optional arguments:
  -h, --help            show this help message and exit

```


## Hostname configuration

```
cortx_setup node prepare network --hostname <hostname>
```

## Server configuration
```
cortx_setup server config --name <server-name> --type {VM|HW}
```

Cortx setup commands are divided into 2 sections 
1. [Factory manufacturing](https://seagate-systems.atlassian.net/wiki/spaces/PUB/pages/502825593/CORTX+Manual+Deployment+onto+3+Node+HW#Factory-Manufacturing)

2. [Field Deployment](https://seagate-systems.atlassian.net/wiki/spaces/PUB/pages/502825593/CORTX+Manual+Deployment+onto+3+Node+HW#Field-Deployment)

We can get details about cortx setup commands in above links.
