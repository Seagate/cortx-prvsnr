# CORTX Provisioning Framework

## Overview
CORTX Provisioner offers a framework which accepts Config Map from CORTX Provisioner, translates into internal configuration and then orchestrates across component mini provisioners to allow them to configure services. In Kubernetes environment, CORTX Provisioner framework runs on all the PODs (in a separate one time container).

***

## CORTX Provisioner Framework Configuration 
CORTX Provisioner needs to be presented with the [solution config parameters](https://seagate-systems.atlassian.net/wiki/spaces/PUB/pages/611615649/CORTX+Configuration+Parameters), which is typically presented at the /etc/cortx/solution/ location as a mounted config map, in kubernetes env. 
Configuration is fed to the CORTX provisioner using the following commands: 
```bash
cortx_setup config apply -f /etc/cortx/solution/cluster.yaml -c yaml:///var/cortx/cluster.conf 
cortx_setup config apply -f /etc/cortx/solution/config.yaml -c yaml:///var/cortx/cluster.conf 
```
**Note:**   
yaml:///etc/cortx/cluster.conf(Local config) is the URL where CORTX configuration is stored for long term. This typically needs to be either hosted on a PVC or a key value serve (e.g. consul:///<consul-server>/key-prefix). 
The same path needs to be passed to the provisioner entry point (cortx_deploy). 
***
## Mini Provisioner Orchestration
There will be CORTX Provisioner Pod for each Service Pod in the system and the scope is limited to that Service Pod only. For example, If there are 15 Service Pods then there would be 15 Provisioner Pods. Provisioner Pod runs all the phases of all the components in a round-robin manner, in sequence for a given Pod only. CORTX K8s Provisioner which orchestrates CORTX Provisioner creates Provisioner Pod and triggers CORTX Provisioner (cortx_setup config apply and bootstrap commands) in all those Pods in parallel. So effectively, all the phases are run in sequence within a Pod but they all run in parallel to other Pods.

Following command is executed to invoke all the mini provisioners within the pod. 
```bash
cortx_setup cluster bootstrap -c yaml:///var/cortx/cluster.conf 
```
