[![Codacy Badge](https://app.codacy.com/project/badge/Grade/f2ba64dc5ca7475d8833f0a3231bb940)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Seagate/cortx-prvsnr&amp;utm_campaign=Badge_Grade)

# Introduction
The purpose of this repository is to provide a provisioning framework for CORTX project.

The objective shall be to
*  Provision an environment (Dev, QA, Lab, Production) with minimal user intervention
*  To maintain modularity/granularity of stages in Provisioning, so as to help enhancements, maintainability and training with minimal collateral impacts
*  To act as single source of truth, reducing confusion of resource references (which is why the reliance would be on Readme.md and GitHub Wiki docs)

# Repo Structure
An overview of folder structure in cortx-prvsnr repo

## api
Files pertaining to Provisioner API are maintained under this directory. These files expose Northbound API, which allows any code external to Provisioner, to use Provisioner API.

## cli
Utility scripts for various provisioning operations.

## devops
Packaging (./devops/rpms), CI and associated scripts.

## docs
Collection of formal and informal documents

## files
Generic files used by Vagrantfile for Vagrant provisioning. These are mere references to possible configurations.

## images
Directory contents provide for creation of images for Docker or Vagrant using Packer and DOckerfiles.

## pillar <sup>[[*](https://docs.saltstack.com/en/latest/topics/pillar/index.html)]</sup>
This is the static data stored as global variables and

## srv
### top.sls
This is the top level state file referred to by highstate when executing SaltStack state(s).

### _modules <sup>[[*](https://docs.saltstack.com/en/latest/ref/states/writing.html#using-custom-state-modules)]</sup>
This directory consists of custom modules.
The `stx_disks.py` is available as a sample module for reference.

### components
This directory is a container for all CORTX software components.
Components implemented and tested:
* [x] Provisioner
* [x] Motr
* [x] S3 Server
* [x] S3 Clients
* [x] Hare
* [x] SSPL
* [x] CSM/Dashboard/Management
* [x] UDS
* [x] Pre-requisites software
  * [x] ha
    * [x] corosync-pacemaker
    * [x] cortx-ha
    * [x] haproxy
* [x] System
  * [x] Time setup (chrony)
  * [x] Firewall
  * [x] Network setup
  * [x] Log rotation
  * [x] Storage setup

Under each of these components/sub-components, a general structure of state files is followed:
* init.sls: Represents highstate of the component module and defines the execution sequence of the state files.
* prepare.sls: This is a preparatory step that sets up the platform before initiating the setup. It shall consist of tasks such as Package repo setup.  
Ensuring any stray files/configs are cleaned, if essential Updating cache for package repositories. Temporary supporting/dependency service stoppages, if need be.
* install.sls: In this step, the provisioner would address all package installation requirements. Packages to be installed include:  
  * RPM  
  * PIP  
Custom build requirements from source tar
* config.sls: This part would be responsible for handling all configuration related tasks. It would consist of:  
  * Copying configuration files to target directories  
  * Modifying the config to suit the target node environment  
  * Execute initialization and configuration scripts  
* housekeeping.sls: Clean-up any temporary directories/files generated during prepare/config state  
* sanity_check.sls: Ensure system is in Green state for the component being set-up. This would be a reusable component  
* teardown.sls: This is a special case that would be triggered only on demand and not as part of normal setup procedure. The purpose of this stage would be to undo all the changes made by all above stages (esp. Install and Config). Ideally after a teardown stage the system would be back to a state as before the start of respective component provisioning.  
* ha.sls: Any ha related script executions shall be handled though this state file.  
* ha_cleanup.sls: Any ha related script executions shall be handled though this state file.  
* refresh_config: Scripts/executions for recovery of config to a sane state should be through this state. 
* backup.sls: backup activities for a given component shall be addressed by this state file.

**Note**: It is not always essential to populate/implement each state file mentioned above.

# User Guide
## SaltStack
### Introduction
https://docs.saltstack.com/en/latest/topics/index.html

#### Initialize Cortx
##### Initalize
1.  Create project folder:
`mkdir ~/projects && cd ~/projects`

1. Clone git repo for cortx-prvsnr:
`git clone https://github.com/Seagate/cortx-prvsnr.git`
`cd ~/projects/cortx-prvsnr`

1. ~~Add Vargrant box created for Cortx:~~  
~~`vagrant box add https://cloud.centos.org/centos/7/vagrant/x86_64/images/CentOS-7-x86_64-Vagrant-1910_01.VirtualBox.box --name centos_7.7.1910`~~

~~##### Start VagrantBox~~  
~~The cortx setup comes with Vagrantfile configured to create a 2 node Vagrant setup. However, due to [limitation with iterations in Vagrantfile](https://www.vagrantup.com/docs/vagrantfile/tips.html), each node needs to be initialized independently:~~  
~~`vagrant up srvnode-1`~~  
~~`vagrant up srvnode-2`~~  

~~##### Synchronize code~~  
~~To synchronize code in git repo on host (`~/projects/cortx-prvsnr`) and `/opt/seagate/cortx/provisioner`:~~  
~~`vagrant rsync`~~  

~~##### Destroy Vagrantbox~~  
~~To cleanup Vagrant setup with deletion of all created boxes and supported virtual hardware:
`vagrant destroy -f`~~  


### Jenkins server
- cleanWS plugin: https://plugins.jenkins.io/ws-cleanup
- junit plugin: https://plugins.jenkins.io/junit
- Branch Source (https://plugins.jenkins.io/github-branch-source) to power Multi Branch pipeline: GitHub
  - Jenkins server:
    - Global Configuration: TODO
    - MBr Pipeline Configuration: TODO
  - GitHub, configure webhooks:
    - URL: <jenkins_url>/github-webhook/post
    - Triggers: Push, Tag, Comments and Merge requests
- optionally:
  - Blue Ocean plugin (https://plugins.jenkins.io/blueocean) to improve UX

## Jenkins agent
- virtualbox
  - plus jenkins user should be added to vboxusers (e.g. usermod -a -G vboxusers jenkins). Note. jenkins node will require reconnection (re-login) after that.
- vagrant
- packer
- python3.6 and pip
- pipenv: pip3 install --user pipenv
- yamllint: pip3 install --user yamllint


For more detailed info , visit our ***[wiki](https://github.com/Seagate/cortx-prvsnr/wiki)*** pages
