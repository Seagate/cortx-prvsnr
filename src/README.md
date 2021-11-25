# CORTX Provisioning Framework

## Overview
CORTX Provisioner offers a framework which accepts Config Map from CORTX Provisioner, translates into internal configuration and then orchestrates across component mini provisioners to allow them to configure services.  

***

## CORTX Provisioner Framework Configuration 
CORTX Provisioner needs to be presented with the [solution config parameters](https://seagate-systems.atlassian.net/wiki/spaces/PUB/pages/611615649/CORTX+Configuration+Parameters).
Configuration is fed to the CORTX provisioner using the following commands: 
```bash
cortx_setup config apply -f <config-path>/cluster.yaml -c <Confstore-URL>
cortx_setup config apply -f <config-path>/config.yaml -c <Confstore-URL>
```
**Note:**   
Confstore-URL is the URL where CORTX configuration is stored for long term. This typically needs to be hosted as a key value serve (e.g. consul:///<consul-server>/key-prefix). 
The same path needs to be passed to the provisioner entry point (cortx_deploy). 
***
## Mini Provisioner Orchestration
There will be CORTX Provisioner Node in the system . Provisioner runs all the phases of all the components in a round-robin manner, in sequence for a given node only. CORTX Provisioner triggers cortx_setup config apply and bootstrap commands in all the nodes in parallel. So effectively, all the phases are run in sequence within a node but they all run in parallel to other nodes.

Following command is executed to invoke all the mini provisioners within the node. 
```bash
cortx_setup cluster bootstrap -c <Confstore-URL>
```
