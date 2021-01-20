#################
Provisioner setup
#################

Overview
********

Main ideas:
- the logic goes through the stages
- the logic is indempotent
- from the configuration phase (once API is setup on target nodes) the
  logic mostly triggesr remote commands so confguration is performed by
  the code version installed on target systems
- each stage and its steps might be run separately using accordant provisioner
  CLI command


The logic has few stages:

- preparation
- installation
- configuration
- start
- validation



Stages
******

Preparation
===========

Preparing setup pillar
----------------------

CLI command: `provisioner setup pillar ...`

Generating setup keys
---------------------

CLI command: `provisioner setup keys...`

Generating a roster file for the setup
--------------------------------------

CLI command: `provisioner setup generate-roster ...`

Ensuring nodes are ready to accept commands
-------------------------------------------

CLI command: `provisioner setup ensure-ready  ...`

??? Resolving node grains
---------------------

CLI command: `provisioner ...`

Setting up paswordless ssh
--------------------------

CLI command: `provisioner setup ssh ...`

Preparing CORTX repos pillar
----------------------------

CLI command: `provisioner setup prepare-cortx-repos-pillar ...`

Installing Cortx yum repositories
---------------------------------

CLI command: `provisioner setup yum-repos ...`

Setting up custom python repository
-----------------------------------

CLI command: `provisioner setup python-repo ...`



Installation
============

Installing SaltStack
--------------------

CLI command: `provisioner setup install-saltstack ...`

Installing provisioner
----------------------

CLI command: `provisioner setup install-provisioner ...`

(optional) Preparing local repo for a setup
-------------------------------------------

Optional: if `local` setup

CLI command: `provisioner setup prepare-local-repo ...`

Installing provisioner API
--------------------------

CLI command: `provisioner setup install-api ...`

Preparing factory profile
-------------------------

CLI command: `provisioner setup prepare-factory-profile ...`

Copying config.ini to file root
-------------------------------

CLI command: `provisioner setup copy-config ...`

Copying factory data
--------------------

CLI command: `provisioner setup copy-factory-data ...`



Configuration
=============

Generating a roster file for the production env
-----------------------------------------------

CLI command: `provisioner setup generate-roster --production ...`

Preparing salt-masters / minions configuration
----------------------------------------------

CLI command: `provisioner setup config-saltstack ...`

Configuring the firewall
------------------------

CLI command: `provisioner setup config-firewall ...`

Configuring glusterfs servers
-----------------------------

CLI command: `provisioner setup config-glusterfs --servers ...`

Configuring glusterfs cluster
-----------------------------

CLI command: `provisioner setup config-glusterfs --cluster ...`

Configuring glusterfs clients
-----------------------------

CLI command: `provisioner setup config-glusterfs --clients ...`

Configuring salt minions
------------------------

CLI command: `provisioner setup config-salt --minions ...`

Configuring salt-masters
------------------------

CLI command: `provisioner setup config-salt --masters ...`

Updating release distribution type
----------------------------------

CLI command: `provisioner setup config-release-pillar --distr ...`

Setting url for bundled dependencies
------------------------------------

CLI command: `provisioner setup config-release-pillar --bundle-url ...`

Updating target build pillar
----------------------------

CLI command: `provisioner setup config-release-pillar --targetr-build ...`

Generating a password for the service user
------------------------------------------

CLI command: `provisioner setup config-service-user ...`

Configuring provisioner logging
-------------------------------

CLI command: `provisioner setup config-logging ...`

Updating BMC IPs
----------------

CLI command: `provisioner setup configure-bmc ...`




Start
=====

Starting salt-masters on all nodes. 
------------------------------------

CLI command: `provisioner setup start-salt-masters ...`

Starting salt minions
---------------------

CLI command: `provisioner setup start-salt-minions ...`

Validation
==========

Ensuring salt-masters are ready
-------------------------------

CLI command: `provisioner setup ensure-salt-masters ...`

Ensuring salt minions are ready
-------------------------------

CLI command: `provisioner setup ensure-salt-minions...`

