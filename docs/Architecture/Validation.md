# Validation Framework

## Table of Contents

*   [General Guidelines](#general-guidelines)

*   [Input/Output Checks](#inputoutput-checks)

    *   [Input Format](#input-format)
    *   [Output Format](#output-format)

*   [Proposed directory structure](#proposed-directory-structure)

*   [`scripts`](#scripts)

    *   [`utils`](#utils)
    *   [`factory`](#factory)
    *   [`field`](#field)

*   [Salt Modules](#salt-modules)

*   [Checks](#checks)

    *   [Hardware check](#hardware-check)

    *   [Software Check](#software-check)

    *   [Provisioner Validations](#provisioner-validations)

    *   [Check API](#check-api)

        *   [Singular Checks](#singular-checks)
        *   [Group Checks](#group-checks)

## General Guidelines

*   As a high-level guideline, the entire framework would be built and managed in Python 3.x+.

    Python helps us in 2 ways:

    1.  Better control over `stdout` and `stderr`.
    2.  Possibility of easily converting Python module to Salt module.

    If you have concerns regarding Python code or lack confidence in Python, it is absolutely ok to capture the logic in a bash script and place it under `_cortx-prvsnr/validation/scripts/utils/uncategorized_`.

*   Another general rule of thumb would be to modularize the checks as much as possible. Avoid long script files. Each script file should contain only checks related to the theme of the file -- ***Single-Responsibility principle***.  E.g. a network check file should have only `ping` test and no checks related to storage connectivity like `iperf`, which also happens over network.

*   Before you start implementing a new check, make sure you have scanned the `utils` directory for any existing modules -- ***Open-Closed principle***.  If you find something similar, but doesn't fit your purpose, consider generalizing the existing module and extend it to scope in the new possible.

*   Any script not in `validation/scripts/utils` should serve the only purpose of making calls to the `util` scripts (**should serve as an orchestrator**). Any specific code logic should be avoided as much as possible. (**Centralization** to avoid regression bugs and enable maintainable code.)

## Input/Output Checks

### Input Format

Ideally the input should be a method call with zero parameters.

If it is necessary to have parameters, there should be only one.

The single parameter shall be a dictionary of all the parameters necessary by the method, with keys as the argument names and values as the potential arguments to the method.  (This would be in-line with Python `**kwargs`).

E.g.:

```python
def foo(
        args = {
            "arg_1": "value_for_arg_1",
            "arg_2": "value_for_arg_2"
        }
    ):
    pass
```

### Output Format

Output shall always be a single JSON format string:

```json
{
  "check": "",  
  "retcode": "",  
  "stdout": "",  
  "stderr": "",  
}
```

Legend:

*   `check`: This is the check that has been performed by the called. It could be the command executed or a short string describing check performed.

*   `retcode`: Return code either from shell for an executed command or a preferable code decided by the called module to help understand the area of failure.

*   `stdout`: The `stdout` from shell command or a string that describes a success scenario.

*   `stderr`: The `stderr` from shell command or a string that describes a failure scenario.

## Proposed directory structure

At a high level the directory structure would consist of:

*   `messages`: Directory for messages. It would consist of:
    *   `user_messages`: Translations for known standard cryptic messages from system (command output/logs).
    *   `log_messages`: Messages that guide the user studying logs. This is essentially required if we plan to do localization in future.
*   `scripts`: The validation scripts performing granular level checks of system processes/components. This directory structure would be discussed in detail in later parts of this document.

A sample tree of directory structure for validation would be:

```bash
    ├───validation
    │   ├───messages
    │   │   ├───user_messages (future_scope: localization)
    │   │   │   ├───error
    │   │   │   └───instructions
    │   │   ├───log_messages (future_scope: localization)
    │   ├───scripts
    │   │   ├───utils
    │   │   │   ├───network_connectivity_check
    │   │   │   ├───internal_storage_connectivity_check
    │   │   │   ├───external_storage_connectivity_check
    │   │   │   ├───raw_io_check_over_sas
    │   │   │   ├───raw_io_check_over_nw
    │   │   │   ├───uncategorized
    |   │   │   |   └───my_custom_check
    │   │   │   └───system_check
    |   │   │       ├───hw_check
    |   │   │       ├───hostname_check
    |   │   │       ├───critical_dir_access_check
    |   │   │       ├───repo_source_check
    |   │   │       ├───gluster_replication_check
    |   │   │       ├───lvm_check
    |   │   │       └───salt_health_check
    │   │   ├───factory
    │   │   │   ├───pre_flight_check
    │   │   │   ├───bootstarp_readiness_check
    │   │   │   ├───deployment_readiness_check
    │   │   │   ├───boxing_readiness_check
    │   │   │   └───system_info
    │   │   └───field
    │   │       ├───hw_check
    │   │       ├───unboxing_readiness_check
    │   │       ├───unboxing_sanity
    │   │       ├───onboarding_readiness_check
    │   │       ├───onboarding_sanity
    │   │       ├───update_readiness_check
    │   │       └───replacement_checks
    |   │           ├───system_check
    |   │           ├───bootstrap_readiness_check
    |   │           ├───bootstrap_success
    |   │           ├───stage_1_readiness_check
    |   │           ├───stage_1_success
    |   │           ├───stage_2_readiness_check
    |   │           ├───stage_2_success
    |   │           └───post_replacement_check
```

## `scripts`

The scripts directory shall be logically segregated into:

*   `utils`
*   `factory`
*   `field`

### `utils`

This would be a common library of reusable modules that would be reused with specific validation scripts targeting a specific logical role.

Example of scripts under `utils` would be:

*   `logger`
*   `exit_trap`
*   `network_connectivity_check`: Tools to test network connectivity
    *   `ping_test`
    *   `port_check`
*   `internal_storage_connectivity_check`: Check storage sanity on server node
*   `external_storage_connectivity_check`: Check storage sanity on storage enclosure
*   `raw_io_check_over_sas`: FIO kind of utility to test IO on SAS channels
*   `raw_io_check_over_nw`: `iperf` kind of utility over IB/TCP channels
*   `system_check`: Various sanity checks for system components (SW/HW):
    *   `hw_check`
    *   `hostname_check`
    *   `critical_dir_access_check`
    *   `repo_source_check`
    *   `gluster_replication_check`
    *   `lvm_check`
    *   `salt_health_check`

### `factory`

The section consists of scripts performing validation in factory environment.
Each logical validation scenario shall represent a script, which aggregates the validation modules from `utils`.

### `field`

The scripts performing validation in field on customer environment.
Each logical validation scenario shall represent a script, which aggregates the validation modules from `utils`.

## Salt Modules

Our salt formula under `srv` directory follows a strict discipline of structure. Thus each component module has `prepare.sls` and `sanity_check.sls`.

In-place validations for each components modules can and shall be performed using:

*   `prepare.sls`: For check prior to starting installation and configuration of a component.
*   `sanity_check.sls`: For check post installation and configuration of a component.

## Checks

### Hardware check

*   Mellanox OFED in installed:

        yum list yum list mlnx-ofed-all

    Ideally pick list of installed packages from

        yum list *mlnx*

    and cross-check against a standard reference list.

*   Mellanox HCA present and has number of ports:

    https://www.mellanox.com/support/firmware/identification

        [root@localhost ~]# lspci -nn | grep "Mellanox Technologies"
        af:00.0 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5] [15b3:1017]
        af:00.1 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5] [15b3:1017]
        d8:00.0 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5] [15b3:1017]
        d8:00.1 Ethernet controller [0200]: Mellanox Technologies MT27800 Family [ConnectX-5] [15b3:1017]

*   LSI HBA is present:

        [root@localhost ~]# lspci -nn | grep "SCSI"
        86:00.0 Serial Attached SCSI controller [0107]: Broadcom / LSI SAS3216 PCI-Express Fusion-MPT SAS-3 [1000:00c9] (rev 01)

*   LSI HBA has required number of ports:
    *   https://www.thegeekdiary.com/how-to-identify-the-hba-cardsports-and-wwn-in-rheloel/
    *   Enclosure volumes are accessible from both servers
        *   `lsblk -S`
        *   `ls -1 /dev/disk/by-id/scsi-*`

*   Enclosure volumes are mapped to both controller:

    (Should be 16 for cross-connect setup with 8 volumes per storage mapping.)

        $ multipath -ll | grep prio=50 | wc -l
          16
        $ multipath -ll | grep prio=10 | wc -l
          16

    If not found, instruct user to run `rescan_scsi_bus.sh`.

*   LVM check:

        $ lvscan | grep metadata | grep ACTIVE | wc -l
        4

    2 for SWAP (one from each node) and 2 for metadata (one for each node).

*   Network interface check:

        $ ip a | grep inet | egrep -v 'inet6|127.0.0.1'
        inet 192.168.10.10/20 brd 10.230.255.255 scope global noprefixroute dynamic eth0
        inet 192.168.20.10/20 brd 192.168.15.255 scope global noprefixroute dynamic eth1
        inet 192.168.30.10/20 brd 192.168.31.255 scope global noprefixroute dynamic eth2

### Software Check

*   Verify rpm:

        yum verify-rpm *cortx*

*   Cluster resource status:

        $ hctl node status --full|jq .
        {
          "resources": {
            "statistics": {
              "started": 71,
              "stopped": 0,
              "starting": 2
            }
          },
          "nodes": [
            {
              "name": "srvnode-1",
              "online": true,
              "standby": false,
              "unclean": false,
              "resources_running": 39
            },
            {
              "name": "srvnode-2",
              "online": true,
              "standby": false,
              "unclean": false,
              "resources_running": 34
            }
          ]
        }

*   Virtual IP:
    *   Cluster VIP on public data network

            $ pcs status | grep kibana-vip
             kibana-vip (ocf::heartbeat:IPaddr2):       Started srvnode-1

            $ salt-call pillar.get cluster:cluster_ip --output=newline_values_only
            172.16.200.11

    *   Management VIP on management network:

            $ pcs status | grep ClusterIP:
             ClusterIP:0        (ocf::heartbeat:IPaddr2):       Started srvnode-1
             ClusterIP:1        (ocf::heartbeat:IPaddr2):       Started srvnode-2
            $ salt-call pillar.get cluster:mgmt_vip --output=newline_values_only
             10.100.200.11

### Provisioner Validations

Certain requirements are mandatory to be available in the setup before and after major processes in Provisioner.\
These verifications have been implemented as part in Provisioner **Validations Framework** to ensure all the mandatory checkpoints are covered and works without any glitches.

### Check API

A new API (***provisioner check***) has been created for this purpose and it can be run on CLI.

`check` api has been created for the below processes:

1.  Before Deployment
2.  After Deployment
3.  Before Unboxing
4.  After Unboxing
5.  Before Node Replacement
6.  Before SW Upgrade

These six categories form the six groups of validations and individual checks will be grouped under either one the above group.

In case of any failure in validations, based on the severity or the significance of the check in the above processes, the flow will either be stopped or the user will be warned of the error and proceeded next.

For example, any error in Pre-Deployment or Pre-Unboxing checks will raise Exception and **the proccess will be stopped right at that step**.\
Whereas, an error in Post-Deployment or Post-Unboxing checks will only raise a Warning with the error details to the user and **the process will continue without any break**.

Though these validations have been seamlessly integrated into the code and are handled as part of the process, they can still be invoked directly on the CLI as,

`provisioner check <check_name>`

#### Singular Checks

    provisioner check network_drivers
    provisioner check network_hca
    provisioner check storage_hba
    provisioner check storage_luns
    provisioner check luns_mapped
    provisioner check storage_lvms
    provisioner check network
    provisioner check connectivity
    provisioner check bmc_accessibility
    provisioner check bmc_stonith
    provisioner check communicability
    provisioner check cluster_status
    provisioner check passwordless_ssh_access
    provisioner check mgmt_vip
    provisioner check hostnames
    provisioner check public_data_ip
    provisioner check controller_ip
    provisioner check logs_are_good

#### Group Checks

    provisioner check deploy_pre_checks
    provisioner check deploy_post_checks
    provisioner check replacenode_checks
    provisioner check swupdate_checks
    provisioner check unboxing_pre_checks
    provisioner check unboxing_post_checks

To execute ALL of the above validations, the below command works,

`provisioner check all`
