# Introduction
The purpose of this repository is to provide a provisioning framework for EOS project.
The objective shall be to
*  Provision an environment (Dev, QA, Lab, Production) with minimal user intervention
*  To maintain modularity/granularity of stages in Provisioning, so as to help enhancements, maintainability and training with minimal collateral impacts
*  To act as single source of truth, reducing confusion of resource references (which is why the reliance would be on Readme.md and GitLab Wiki docs)

# Repo Structure
An overview of folder structure in eos-prvsnr repo
## files
Generic files used by Vagrantfile for Vagrant provisioning.

## pillar <sup>[[*](https://docs.saltstack.com/en/latest/topics/pillar/index.html)]</sup>
This is the static data stored as global variables and

## srv
### top.sls
This is the top level state file referred to by highstate when executing SaltStack state(s).

### _grains <sup>[[*](https://docs.saltstack.com/en/latest/topics/grains/index.html#writing-grains)]
This directory consists of custom grains.
It has a module to fetch MAC address and IP address data over IPMI and present it as `bmc_network` grain item.

### _modules <sup>[[*](https://docs.saltstack.com/en/latest/ref/states/writing.html#using-custom-state-modules)]</sup>
This directory consists of custom modules.
The `stx_disks.py` is available as a sample module for reference.

### components
This directory is a container for all EOS software components.
Components implemented and tested:
* [x] SSPL
* [x] Mero
* [x] Halon
* [x] S3 Server
* [ ] CSM/Dashboard/Management
* [ ] Peripheral support software
  * [ ] ha
    * [ ] corosync
    * [ ] keepalived
  * [ ] loadbalancer
    * [ ] haproxy
* [ ] System
  * [ ] Log rotation
  * [ ] Time setup
  * [ ] Disk setup
  * [ ] `/etc/hosts` file setup
  * [ ] Network setup

Under each of these components/sub-components, a general structure of state files is followed:
* init.sls: Represents highstate of the component module and defines the execution sequence of the state files.
* prepare.sls: This is a preparatory step that sets up the platform before initiating the setup. It shall consist of tasks such as
Package repo setup
Ensuring any stray files/configs are cleaned, if essential
Updating cache for package repositories
Temporary supporting/dependency service stoppages, if need be
* install.sls: In this step, the provisioner would address all package installation requirements. Packages to be installed include
RPM
PIP
Custom build requirements from source tar
* config.sls: This part would be responsible for handling all configuration related tasks. It would consist of:
Copying configuration files to target directories
Modifying the config to suit the target node environment
Execute initialization and configuration scripts
* housekeeping.sls: Clean-up any temporary directories/files generated during prepare/config state
* sanity_check.sls: Ensure system is in Green state for the component being set-up. This would be a reusable component
* teardown.sls: This is a special case that would be triggered only on demand and not as part of normal setup procedure. The purpose of this stage would be to undo all the changes made by all above stages (esp. Install and Config). Ideally after a teardown stage the system would be back to a state as before the start of respective component provisioning.

**Note**: It is not always essential to populate/implement each state file mentioned above.

# Environments
## Dev Setup
For environment specific details please refer to:
http://gitlab.mero.colo.seagate.com/eos/provisioner/eos-prvsnr/wikis/Dev-Setup

## Factory Setup

## Lab Setup

## QA Setup

# User Guide
## SaltStack
### Introduction
https://docs.saltstack.com/en/latest/topics/index.html

### Provisioning EOS Components
#### Platform

#### SSPL

#### Mero

#### Halon

#### S3Server

## Vagrant
### Introduction

### Setup VirtualBox

### Setup Vagrant

#### Initialize EES
##### Initalize
1.  Create project folder:
`mkdir ~/projects && cd ~/projects`

1. Clone git repo for ees-prvsnr:
`git clone http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr/`
`cd ~/projects/ees-prvsnr`

1. Add Vargrant box created for EES:
`vagrant box add http://ci-storage.mero.colo.seagate.com/prvsnr/vendor/centos/vagrant.boxes/centos_7.5.1804.box --name centos_7.5.1804`

##### Start VagrantBox
The ees setup comes with Vagrantfile configured to create a 2 node Vagrant setup. However, due to [limitation with iterations in Vagrantfile](https://www.vagrantup.com/docs/vagrantfile/tips.html), each node needs to be initialized independently:
`vagrant up ees-node1`
`vagrant up ees-node2`

##### Synchronize code
To synchronize code in git repo on host (`~/projects/ees-prvsnr`) and `/opt/seagate/eesprvsnr`:
`vagrant rsync`

##### Destroy Vagrantbox
To cleanup Vagrant setup with deletion of all created boxes and supported virtual hardware:
`vagrant destroy -f`

## TBD
- [ ] add proper description
- [ ] add actual code
- [x] add automatic mirroring to SeaGit
