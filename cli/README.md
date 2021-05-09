[[_TOC_]]

# The Provisioner Setup Scripts

This folder includes scripts that simplify provisioning of the CORTX stack providing a set of CLI utils:

- [src](src) folder consists of shell scripts that automate initial environment installation, salt configuration and salt formulas appliance

## Shell Scripts

Each script prints help with details regarding its usage, please use `-h`/`--help` for that.

The scripts might be applied to either remote or local hosts and have some prerequisites regarding the hosts state.
It means they should be called in the following predefined order:
1. `setup-provisioner`: installs and configures SaltStack, installs provisioner repo and setup SaltStack master-minion connections
2. `configure`: adjusts pillars for provisioner components
3. `deploy`: installs CORTX stack using Salt
4. `bootstrap`: initializes CORTX services
5. `start`: starts/restarts CORTX services
6. `stop`: stops CORTX services

### Common Options

Besides help options each script might be called using any of the following options:

- ~~`-r`/`--remote`: specifies the hostspec of the remote host. When passed the script performs its commands against remote host instead of the local one.~~
- `-S`/`--singlenode`: turns on single mode installation. Makes sense not for all scripts.
- `-F`/`--ssh-config`: allows to specify an alternative path to ssh configuration file which is likely makes sense in case of remote host configuration.
- `-v`/`--verbose`: tells the script to be more verbose.

[//]: #   (commented by EOS-2410)
[//]: #   (- `-n`/`--dry-run`: do not actually perform any changes)
[//]: #   (- `-s`/`--sudo`: tells the script to use `sudo`.)

~~#### Remote hosts configuration~~

~~If you have to deal with a remote host or even with a set of remote hosts you will likely want to prepare a ssh configuration file. The file might include hosts specification along with paths to private ssh keys, ssh connection parameters etc.~~

~~For that case you can use `-F`/`--ssh-config` option along with `-r`/`--remote` to specify a remote host spec, e.g.:~~

$ `setup-provisioner -F ./ssh_config ` ~~`-r srvnode-1`~~


where `./ssh_config` might look like:

```
Host srvnode-1
    HostName <srvnode-1-HOSTNAME-OR-IP-1>
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile <PATH-TO-SSH-KEY>
    IdentitiesOnly yes

Host srvnode-2
    HostName <srvnode-2-HOSTNAME-OR-IP>
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile <PATH-TO-SSH-KEY>
    IdentitiesOnly yes
```

### setup-provisioner

Installs the provisioner repository along with SaltStack on the hosts with bare OS installed, configures salt-master/salt-minion connections and makes some additional preliminary configuration.

Besides [general](#common-options) set of options it expects the following ones:

- `--srvnode-2=[user@]hostname`: sets host specification of the srvnode-2. If missed default one is assumed: `srvnode-2`.
- `--repo-src={local|github|rpm}`: configures the source of the provisioner repository to use during installation:
  - `local` to install current working copy of the repository on on the host;
  - `github` to install from Github by provided version (see below);
  - `rpm` to install from using rpm package (default).
- `--salt-master=HOSTNAME` the hostname/IP to use to configure salt minions connections to salt-master.
  By default it is not set the script will try to discover it itself. As a final fallback the default
  value will be used (it is specified in salt minion's [config file](../cortx/srv/provisioner/salt_minion/files/minion)
  and is `srvnode-1` for now).

Also the script expects one optional positional argument to specify a version of the provisioner repository to install.
For now that makes sense only for `github` and if missed the latest tagged version would be installed.

#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)

#### Examples

Configure cluster with a salt-master on srvnode-1

```shell
$ setup-provisioner -F ./ssh_config --salt-master=<SRVNODE-1-IP>
```

### configure-cortx

Configures cortx services either on remote host or locally for a specified configuration component.

Usually the only component that need additional configuration are `cluster` and `release`.

Accepts the following custom options:

- `-f`/`--file`: specifies path to file with updated pillar data for the component.
- `-p`/`--show-file-format`: a flag to just show current pillar data for the component and exit.


The only positional argument (which is expected and required) is the component name (e.g. `release`, `cluster`, `sspl` ...).

#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)
2. provisioner repo is installed

#### Examples

Show configuration file skeleton for the cluster component against locally installed provisioner

```shell
$ configure cluster --show-file-format
```

Show configuration file skeleton for the cluster component against remotely installed provisioner

```shell
$ configure cluster --show-file-format --remote user@host
```

Update the pillar for the release component remotely using specified file as a source

```shell
$ configure release --file ./release.sls --remote user@host
```

### deploy-cortx

Installs CORTX stack and configures cortx services either on remote host or locally by calling salt apply command for the components.

No specific options or positional arguments are expected by the script.

#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)
2. provisioner repo is installed
3. SaltStack is installed
4. salt master-minion connections are configured
5. networks are configured
6. cluster and release pillars are adjusted

#### Examples

Install CORTX stack for a cluster with a local host as srvnode-1

```shell
$ deploy
```

Install CORTX stack for a cluster with a remote host as srvnode-1

```shell
$ deploy -r srvnode-1 -F ./ssh_config
```

Install CORTX stack for a single node with a remote host as srvnode-1

```shell
$ deploy -r srvnode-1 -F ./ssh_config --singlenode
```

### bootsrap-cortx

Initializes CORTX services either on remote host or locally.

As it has similar cli API as [deploy-cortx](#deploy-cortx) please refer to the latter for usage examples.


#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)
2. provisioner repo is installed
3. SaltStack is installed
4. salt master-minion connections are configured
5. networks are configured
6. cluster and release pillars are adjusted
7. CORTX Stack is installed


### start-cortx

Starts all CORTX services either on remote host or locally.

Restart CORTX services if `--restart` flag is explicitly specified.

As of now the script performs the same operations for cluster and single node installations.
But that might be changed in future.


#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)
2. provisioner repo is installed
3. SaltStack is installed
4. salt master-minion connections are configured
5. networks are configured
6. cluster and release pillars are adjusted
7. CORTX Stack is installed
8. CORTX Stack is bootstrapped


#### Examples

Start all services for a cluster with local host as srvnode-1

```shell
$ start
```

Start all services for a cluster with remote host as srvnode-1

```shell
$ start --remote srvnode-1 -F ./ssh_config
```

Restart all services for a cluster with remote host as srvnode-1


```shell
$ start --remote srvnode-1 -F ./ssh_config --restart
```

### stop-cortx

Stop all CORTX services either on remote host or locally.

No specific options or positional arguments are expected by the script.

As of now the script perform the same operations for cluster and single node installations.
But that might be changed in future.

#### Examples

Stop all services for a cluster with local host as srvnode-1

```shell
$ stop
```

Stop all services for a cluster with remote host as srvnode-1

```shell
$ stop --remote srvnode-1 -F ./ssh_config
```

### End-to-End Examples

#### Singlenode local installation

**Note**: requires to be run under `root` user.

1. `setup-provisioner -S`
2. `configure -p cluster >./cluster.sls`
3. ... edit `cluster.sls` manually ...
4. `configure -f ./cluster.sls cluster`
5. `configure -p release >./release.sls`
6. ... edit `release.sls` manually ...
7. `configure -f ./release.sls release`
8. `deploy -S`
9. `bootstrap -S`
10. `start -S`

#### Singlenode remote installation

Remote installation requires ssh configuration:
- ssh keypair should be created (e.g. `ssh-keygen -t rsa -b 4096 -o -a 100 -C "your_email@example.com" -f ./id_rsa.cortx`)
- public key should be added for the `root`'s user (`/root/.ssh/authorized_keys`) on a remote host
- local ssh-configuration file should be prepared

**Note**: `root` user is not required on a local system.

Example of a ssh-config file:

```
Host srvnode-1
    HostName <ip/domain-name>
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile ./id_rsa.cortx
    IdentitiesOnly yes
```

Steps are exactly the same with the only difference: all scripts calls should include options `-r srvnode-1 -F ./ssh_config`. Where `./ssh_config` is a path to the prepared ssh configuration file and `srvnode-1` is an ID of the host described in that file.

#### Cluster local installation

**Note 1**: since primary node is a localhost the following requires to be run under `root` user.

**Note 2**: Cluster installation for both local and remote modes requires ssh configuration since even for a local installation secondary node is supposed to be a remote host. At the same time:
- configuation is required only for the secondary node
- only `setup-provisioner` should be supplied with the configuration file. Other scripts will perform local operations only.

Please refer to [Singlenode remote installation](#singlenode-remote-installation) regarding the details.

Example of a ssh-config file:

```
Host srvnode-2
    HostName <ip/domain-name>
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile ./id_rsa.cortx
    IdentitiesOnly yes
```

1. `setup-provisioner -F ./ssh_config --salt-master <HOST>` (where `HOST` is IP / domain name of the primary node reachable from the secondary one)
2. `configure -p cluster >./cluster.sls`
3. ... edit `./cluster.sls` manually ...
4. `configure -f ./cluster.sls cluster`
5. `configure -p release >./release.sls`
6. ... edit `./release.sls` manually ...
7. `configure -f ./release.sls release`
8. `deploy`
9. `bootstrap`
10. `start`


#### Cluster remote installation

**Note**. The differences with the [local cluster installation](#cluster-local-installation) are:
- ssh config file should include specifications for both primary and secondary node
- all scripts require remote connections specification (e.g. `-r srvnode-1 -F ./ssh_config`)

Example of a ssh-config file:

```
Host srvnode-1
    HostName <ip1/domain-name1>
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile ./id_rsa.cortx
    IdentitiesOnly yes

Host srvnode-2
    HostName <ip2/domain-name2>
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile ./id_rsa.cortx
    IdentitiesOnly yes
```
