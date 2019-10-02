# The Provisioner Setup Scripts

This folder includes scripts that simplify provisioning of the EOS stack providing a set of CLI utils:

- [src](src) folder consists of shell scripts that automate initial environment installation, salt configuration and salt formulas appliance

## Shell Scripts

Each script prints help with details regarding its usage, please use `-h`/`--help` for that.

The scripts might be applied to either remote or local hosts and have some prerequisites regarding the hosts state.
It means they should be called in the following predefined order:
1. `setup-provisioner`
2. `configure-eos`
3. `deploy-eos`
4. `bootstrap-eos`
5. `start-eos`
6. `stop-eos`

### Common Options

Besides help options each script might be called using any of the following options:

  - `-n`/`--dry-run`: do not actually perform any changes (_not fully supported for now_)
  - `-r`/`--remote`: specifies the hostspec of the remote host. When passed the script performs its commands against remote host instead of the local one.
  - `-S`/`--singlenode`: turns on single mode installation. Makes sense not for all scripts.
  - `-F`/`--ssh-config`: allows to specify an alternative path to ssh configuration file which is likely makes sense in case of remote host configuration.
  - `-s`/`--sudo`: tells the script to use `sudo` (_not enough tested yet_).
  - `-v`/`--verbose`: tells the script to be more verbose.

#### Remote hosts configuration

If you have to deal with a remote host or even with a set of remote hosts you will likely want to prepare a ssh configuration file. The file might include hosts specification along with paths to private ssh keys, ssh connection parameters etc.

For that case you can use `-F`/`--ssh-config` option along with `-r`/`--remote` to specify a remote host spec, e.g.:

```shell
$ setup-provisioner -F ./ssh_config -r eosnode-1
```

where `./ssh_config` might look like:

```
Host eosnode-1
    HostName <EOSNODE-1-HOSTNAME-OR-IP-1>
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile <PATH-TO-SSH-KEY>
    IdentitiesOnly yes

Host eosnode-2
    HostName <EOSNODE-2-HOSTNAME-OR-IP>
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile <PATH-TO-SSH-KEY>
    IdentitiesOnly yes
```

### setup-provisioner

Installs the provisioner repository along with SaltStack on the hosts with bare OS installed, configures salt master/minion connections and makes some additional preliminary configuration.

Besides [general](#common-options) set of options it expects the following ones:

- `--eosnode-2=[user@]hostname`: sets host pecification of the eosnode-2. If missed default one is assumed: `eosnode-2`.
- `--repo-src={local|gitlab|rpm}`: configures the source of the provisioner repository to use during installation:
  - `local` to install current working copy of the repository on on the host;
  - `gitlab` to install from GitLab by provided version (see below);
  - `rpm` to install from using rpm package.
- `--salt-master=HOSTNAME` the hostname/IP to use to configure salt minions connections to master. By default it is not set which means that default SaltStack value will be set (which is `salt`).

Also the script expects one optional positional argument to specify a version of the provisioner repository to install.
For now that makes sense only for `gitlab` and if missed the latest tagged version would be installed.

#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)

#### Examples

Configure cluster with a master on eosnode-1

```shell
$ setup-provisioner -r eosnode-1 -F ./ssh_config --salt-master=<EOSNODE-1-IP>
```

### configure-eos

Configures eos services either on remote host or locally for a specified configuration component.

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
$ configure-eos cluster --show-file-format
```

Show configuration file skeleton for the cluster component against remotely installed provisioner

```shell
$ configure-eos cluster --show-file-format --remote user@host
```

Update the pillar for the release component remotely using specified file as a source

```shell
$ configure-eos release --file ./release.sls --remote user@host
```

### deploy-eos

Installs EOS stack and configures eos services either on remote host or locally by calling salt apply command for the components.

No specific options or positional arguments are expected by the script.

#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)
2. provisioner repo is installed
3. SaltStack is installed
4. salt master-minion connections are configured
5. networks are configured
6. cluster and release pillars are adjusted

#### Examples

Install EOS stack for a cluster with a local host as eosnode-1

```shell
$ deploy-eos
```

Install EOS stack for a cluster with a remote host as eosnode-1

```shell
$ deploy-eos -r eosnode-1 -F ./ssh_config
```

Install EOS stack for a single node with a remote host as eosnode-1

```shell
$ deploy-eos -r eosnode-1 -F ./ssh_config --singlenode
```

### bootsrap-eos

Initializes EOS services either on remote host or locally.

As it has similar cli API as [deploy-eos](#deploy-eos) please refer to the latter for usage examples.


#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)
2. provisioner repo is installed
3. SaltStack is installed
4. salt master-minion connections are configured
5. networks are configured
6. cluster and release pillars are adjusted
7. EOS Stack is installed


### start-eos

Starts all EOS services either on remote host or locally.

Restart EOS services if `--restart` flag is explicitly specified.

As of now the script performs the same operations for cluster and single node installations.
But that might be changed in future.


#### Prerequisites

1. (remote installation) ssh is configured (ssh server is running, keys are set)
2. provisioner repo is installed
3. SaltStack is installed
4. salt master-minion connections are configured
5. networks are configured
6. cluster and release pillars are adjusted
7. EOS Stack is installed
8. EOS Stack is bootstrapped


#### Examples

Start all services for a cluster with local host as eosnode-1

```shell
$ start-eos
```

Start all services for a cluster with remote host as eosnode-1

```shell
$ start-eos --remote eosnode-1 -F ./ssh_config
```

Restart all services for a cluster with remote host as eosnode-1


```shell
$ start-eos --remote eosnode-1 -F ./ssh_config --restart
```

### stop-eos

Stop all EOS services either on remote host or locally.

No specific options or positional arguments are expected by the script.

As of now the script perform the same operations for cluster and single node installations.
But that might be changed in future.

#### Examples

Stop all services for a cluster with local host as eosnode-1

```shell
$ stop-eos
```

Stop all services for a cluster with remote host as eosnode-1

```shell
$ stop-eos --remote eosnode-1 -F ./ssh_config
```
