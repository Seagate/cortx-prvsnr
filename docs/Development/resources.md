# Provisioner Resource Base Approach of System Configuration

The current document explains modular based approach when each SW/HW component
is a "resource" with a set possible states and configuration parameters
per state.

## Table of Contents

*   [Overview](#overview)

*   [The Classes](#the-classes)

    *   [Base Abstractions](#base-abstractions)

    *   [Supported Resources](#supported-resources)

    *   [Resource Managers](#resource-managers)

        *   [SaltStack Manager](#saltstack-manager)

    *   [CLI Interfaces (Examples of Usage)](#cli-interfaces-examples-of-usage)

        *   [Environment Preparation](#environment-preparation)
        *   [Cortx Repos setup](#cortx-repos-setup)
        *   [SaltStack cluster setup](#saltstack-cluster-setup)

## Overview

Main points:

*   each SW/HW component is treated as a system **resource**
*   for each resource we define the **states**
*   each state may require a set of input **state parameters** which define it
*   to move a resource to a state (with defined set of parameters)
    a **transition** should be implemented
*   tansition can be implemented using different tools (e.g. Ansible, SaltStack
    or just bash)
*   we support **only SaltStack currently**
*   **resource manager** is one more abstraction here: it keeps a transitions
    registry and provides
    a high level interface to move a resource into the desired state

SaltStack transitions:

*   transition logic is presented as Salt formulas
*   a formula relies on Salt env which are pillar variables and files in Salt
    file roots
*   python layer provides CLI and python API interfaces and implements mapping
    between state parameters as inpurs and Salt env (pillar and fileroot entries)

## The Classes

TBD component/classes diagram

### Base Abstractions

The changes include implementation of the base abstractions

*   `ResourceBase` - base class for a resource
*   `ResourceParams` - base class for resource parameters
*   `ResourceState` - base class for a resource state
*   `ResourceTransition` - base class for a transition
*   `ResourceManager` - base class for a resource manager

### Supported Resources

Each resource provides both CLI and python API interfaces so you
can setup a resource using both shell or programmatically from pyton code.

The following resource are available:

*   `CortxRepos` - Cortx deployment repositories
*   group of SaltStack resources:
    *   `SaltMinion`
    *   `SaltMater`
    *   `SaltStack` - common logic
    *   `SaltCluster` - implements logic of Salt cluster configuration
        over salt-minions and salt-masters
*   `Consul`

### Resource Managers

#### SaltStack Manager

*   `SLSResourceManager`: it is the only resource manager that Provisioner
    supports for the moment.

Transitions list is discovered automatically.

### CLI Interfaces (Examples of Usage)

#### Environment Preparation

Setup docker and python environment as described
[here](https://github.com/Seagate/cortx-prvsnr/blob/pre-cortx-1.0/docs/testing.md).

Create docker containers (please check
[testing.md](docs/Development/testing.md) for the details):

```bash
pytest test/build_helpers -k test_build_setup_env -s [--docker-mount-dev] --nodes-num 3
```

Notes:

*   by default it would set `root` as a password for root user there
*   in output you will see ssh configuration along with path to ssh-config file
*   that command will prompt you to press a key to proceed (exit),
    so you can either move it to the background or proceed in another terminal
    with activated python venv

Generate local profile to be used later for all remote setup commands:

```bash
# generates ssh profile
provisioner helper generate-profile --profile-name myprofile --cleanup`

# ensures nodes are ready for the setup routine
SSHPASS=root provisioner helper ensure-nodes-ready \
    --profile-name myprofile srvnode-1:<IP1> srvnode-2:<IP2> srvnode-3:<IP3>
```

Notes:

*   You can find the profile in `$HOME/.provisioner` folder.
*   values of `IP*` might be get from ssh configuration mentioned above
*   without SSHPASS the second command would prompt you for root password for an
    initial access to the nodes
*   an alternative way is to pass a key from ssh configuration as `--ssh-key`
    (would be used for access) or as `--bootstrap-key` (would be used for
    initial access only). In both cases root password will not be required.

#### Cortx Repos setup

Run the following command to setup Cortx repositories using an ISO:

```bash
provisioner resource cortx_repos setup --dist-type bundle \
    --salt-client-type ssh --salt-ssh-profile-name myprofile <PATH-TO-BUNDLE>
```

Notes:

*   `PATH-TO-BUNDLE` is path to a single repo image used currently for deployment.
    You can either use one provided by Seagate or build a mock as descibed in
    [testing.md](docs/Development/testing.md)
*   `--dist-type cortx` is also supported and implies a flat yum repository with
    only cortx packages inside

#### SaltStack cluster setup

Setup salt's vanilla repos:

```bash
provisioner resource saltstack repo \
    --salt-client-type ssh --salt-ssh-profile-name myprofile

# verify
provisioner salt ssh --profile-name myprofile cmd.run \
    --fun-args 'yum list available | grep salt' --out json
```

Install salt-minions on all the nodes:

```bash
provisioner resource salt-minion install --salt-client-type ssh \
    --salt-ssh-profile-name myprofile

# verify
provisioner salt ssh --profile-name myprofile cmd.run \
    --fun-args 'salt-minion --version' --out json
```

Install masters salt-masters on all the nodes (but might be targetted differently):

```bash
provisioner resource salt-master install \
    --salt-client-type ssh --salt-ssh-profile-name myprofile

# verify
provisioner salt ssh --profile-name myprofile cmd.run \
    --fun-args 'salt-master --version' --out json
```

Stop services:

```bash
provisioner resource salt-master stop --salt-client-type ssh \
    --salt-ssh-profile-name myprofile

provisioner resource salt-minion stop --salt-client-type ssh \
    --salt-ssh-profile-name myprofile
```

Config the cluster:

```bash
provisioner resource salt-cluster config \
    --onchanges-minion stop --onchanges-master restart \
    --salt-client-type ssh --salt-ssh-profile-name myprofile
```

Start services:

```bash
provisioner resource salt-master start \
    --salt-client-type ssh --salt-ssh-profile-name myprofile

provisioner resource salt-minion start \
    --salt-client-type ssh --salt-ssh-profile-name myprofile
```

Verify minions are connected to all the masters:

```bash
provisioner salt ssh --profile-name myprofile cmd.run \
    --fun-args 'salt-run manage.up' --out json
```
