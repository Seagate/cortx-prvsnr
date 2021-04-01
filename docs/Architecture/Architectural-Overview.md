
Table of Contents

- [Use of SaltStack](#use-of-saltstack)
- [High Level Repository Structure](#high-level-repository-structure)
  - [Repo Structure](#repo-structure)
    - [`files`](#files)
    - [`pillar`](#pillar)
    - [`srv`](#srv)
      - [`top.sls`](#topsls)
      - [`_grains`](#_grains)
      - [`_modules`](#_modules)
      - [`components`](#components)


# Use of SaltStack

SaltStack has 3 possible modes of operation that were tried out before arriving on the final approach:

* SSH: This mechanism is similar to Ansible, which primarily performs remote executions over SSH protocol. Salt-SSH requires each node to be configured in roster file and thus the execution is limited to the number of entries in Roster file.

  cortx-prvsnr uses Salt-SSH for initial provisioner bootstrap. This installs and configures Salt in master-minion configuration along with cortx-prvsnr itself.

  The cortx-prvsnr API (`provisioner --help`) provides various commands to perform this bootstrap on various environments and is also capable of remotely performing bootstrap on a system from a jump server/host.

* Masterless: Salt formulae would be executed on each minion independently in absence of Salt master (using salt-call --local). This has lower overhead and works fine with single node configuration.

  With multi-node configuration, the setup still was workable, however, the source of Salt formulae (cortx-prvsnr repo) requires replication on each node. Also, assigning role to each node independently becomes challenging.

  This mechanism is preferred to make local calls to fetch data (grains/pillar) from Salt.

* Master-Minion: Primary node is elected as Salt master and minions installed on primary and non-primary nodes are connected to the master. This configuration allows better source code management, centralized control and possibility to remotely trigger execution using delegation (salt-syndic).
  
  Master-Minion configuration is the backbone of cortx-prvsnr. Deployment, updates, Northbound API execution (and monitoring in future) are all designed around the capability of salt-minions to communicate with salt-master. This configuration allows for scalability and asynchronous mode of operations.


# High Level Repository Structure

The provisioner code is broken down into 3 essential parts:

* State files (`./srv`)
* Static configuration data (`./pillar`)
* Application Programming Interface (`./api`)
* Command Line Interface (`./cli`)

## Repo Structure

An overview of folder structure in cortx-prvsnr repo:

### `files`

Generic files used by Vagrantfile for Vagrant provisioning.  

### `pillar`

Pillar is an interface for Salt designed to offer global values that can be distributed to minions.  See [Salt Docs](https://docs.saltstack.com/en/latest/topics/pillar/) for more details.

For EOS and supported components the pillar data is maintained under:

* Repo path: `./pillar/components`
* Installed path: `/opt/seagate/cortx/provisioner/pillar/components`

NOTE: User modified pillars are not stored at above location as their data would be replaced during updates.

It's recommended that the Pillar data should be updated using `provisioner pillar_set`, although currently it's possible to update these files manually.

### `srv`

#### `top.sls`

This is the top level state file referred to by highstate when executing SaltStack state(s).  

#### `_grains`

See also [Salt Docs on Grains](https://docs.saltstack.com/en/latest/topics/grains/index.html#writing-grains).

This directory consists of custom grains.

It has a module to fetch MAC address and IP address data over IPMI and present it as `bmc_network` grain item.

#### `_modules`

See also [Salt Docs on Modules](https://docs.saltstack.com/en/latest/ref/states/writing.html#using-custom-state-modules).

This directory consists of custom modules.

The `stx_disks.py` is available as a sample module for reference.

#### `components`

These are the Salt state formulae. They are categorized into components and sub-components under `./src/components`.

Each EOS component represents a folder. There are other components which are either common (covered under `./srv/components/misc` and `./srv/components/ha`) and system level configurations (covered under `./srv/components/system`).

Sub-components are sub-directories under `./srv/components/<component>`.

As of writing the components directory looks like:

```
├───srv  
│   ├───components  
│   │   ├───csm  
│   │   ├───motr  
│   │   ├───ha  
│   │   │   ├───corosync-pacemaker  
│   │   │   ├───haproxy  
│   │   │   └───keepalived  
│   │   ├───hare  
│   │   ├───misc  
│   │   │   ├───build_ssl_cert_rpms  
│   │   │   ├───elasticsearch  
│   │   │   ├───kibana  
│   │   │   ├───lustre  
│   │   │   ├───nodejs  
│   │   │   ├───openldap  
│   │   │   └───rabbitmq  
│   │   ├───performance_testing  
│   │   │   └───cosbench  
│   │   ├───post_setup  
│   │   ├───s3client  
│   │   │   ├───awscli  
│   │   │   └───s3cmd  
│   │   ├───s3server  
│   │   ├───sspl  
│   │   └───system  
│   │       ├───logrotate  
│   │       ├───network  
│   │       ├───ntp  
│   │       └───storage  
```

Each component/sub-component directory should consist of an `.sls` (Salt state) file or directory with collection of state files each addressing execution steps in entirety (attempting to following single responsibility principle).  Supported states are listed below:

* `init`: Represents highstate of the component module and defines the execution sequence of the state files.

* `prepare`: This is a preparatory step that sets up the platform before initiating the setup.  It shall consist of tasks such as:
  * Package repo setup.
  * Ensuring any stray files/configs are cleaned, if essential.
  * Updating cache for package repositories.
  * Temporary supporting/dependency service stoppages, if need be.
  * Pre-checks before the components installation, configuration is attempted.

* `install`: Installation of component and its requisite packages. It is expected that the component package to include all the required dependencies. However, in absence of component package's ability to have all requisites installed, provisioner would address such installation from this file/directory.

  Packages types to be installed include:

  * RPM/DEB
  * PIP
  * Custom build requirements from source tar

* `config`: Any configurations required for base (factory/field) setup of the component shall be covered in this file/directory. In ideal world, this would be a simple call to component provided `init` file. This state file should also allow for correcting any deviations caused by user over-rides.
A representative config directory structure shall be:
```
├───component
│   ├───config
│   │   ├───init
│   │   ├───post_install
│   │   ├───config
│   │   ├───init_mod

```

Each sub-level file would consist of calls to respective southbound API as:
* `init`: Represent states of the configuration and defines the execution sequence of the state files within config.
* `post_install` : After installing the component , post_install call will be made through `/opt/seagate/cortx/csm/conf/setup.yaml` and it will call `[component]:post_install` command.
* `config` : Copying configuration files to target directories and Modifying the Configuration to suit the target node environment will be covered from config , and these steps will be invoked from config command respective to the component.
* `init_mod` : Execute initialization and configuration scripts of component will get covered with init_mod.


* `start`: Start component services.
* `stop`: Stop component services.

* `housekeeping`: Any expected clean-up activities for junk files created during setup and if required, during operation phase.

* `sanity_check`: This is a crucial stage as its outcome would determine and confirm the healthy state of the component in operation (post setup). This should be an independently reusable component.

* `teardown.sls`: This is a special case that would be triggered only on demand and not as part of normal setup procedure. The purpose of this stage would be to undo all the changes made by all above stages (esp. Install and Config). Ideally after a teardown stage the system would be back to a state as before the start of respective component provisioning.

**Note**: It is not always essential to populate/implement each state file mentioned above.
