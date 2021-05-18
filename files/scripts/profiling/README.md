# Steps to use this script  

- During deployment, save the output of the provisioner auto_deploy_vm command in some file.**

```sh
provisioner auto_deploy_vm srvnode-1:ssc-vm-c-1810.colo.seagate.com --logfile --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm --config-path ~/config.ini --dist-type bundle --target-build http://<cortx_release_server>/releases/cortx_builds/centos-7.8.2003/531/ | tee deploy_log 
```

```sh
$ cat deploy_log
2021-01-06 17:30:03,575 - INFO - Setup provisioner
2021-01-06 17:30:03,577 - INFO - Starting to build setup 'srvnode-1_root@ssc-vm-c-1810.colo.seagate.com_22'
2021-01-06 17:30:03,581 - INFO - Profile location '/root/.provisioner/srvnode-1_root@ssc-vm-c-1810.colo.seagate.com_22'
2021-01-06 17:30:03,581 - INFO - Preparing setup pillar
2021-01-06 17:30:03,584 - INFO - Generating setup keys
2021-01-06 17:30:03,899 - INFO - Generating a roster file
2021-01-06 17:30:03,900 - INFO - Copying config.ini to file root
2021-01-06 17:30:03,905 - INFO - Preparing CORTX repos pillar
2021-01-06 17:30:03,929 - INFO - Ensuring 'srvnode-1' is ready to accept commands
Password:
2021-01-06 17:30:14,348 - INFO - Resolving node grains
2021-01-06 17:30:18,226 - INFO - Preparing salt-masters / minions configuration
2021-01-06 17:30:24,463 - INFO - srvnode-1 is reachable from other nodes by: {'192.168.31.237', 'ssc-vm-c-1810.colo.seagate.com', '10.230.240.251', '192.168.12.71', 'ssc-vm-c-1810'}
2021-01-06 17:30:24,465 - INFO - salt-masters would be set as follows: {'srvnode-1': ['127.0.0.1']}
2021-01-06 17:30:27,467 - INFO - Preparing factory profile
2021-01-06 17:30:27,509 - INFO - Installing Cortx yum repositories
2021-01-06 17:30:35,401 - INFO - Setting up custom python repository
2021-01-06 17:30:38,782 - INFO - Checking paswordless ssh
2021-01-06 17:30:42,165 - INFO - Configuring the firewall
2021-01-06 17:30:45,746 - INFO - Installing SaltStack
2021-01-06 17:31:10,109 - INFO - Installing provisioner from a 'rpm' source
2021-01-06 17:31:21,344 - INFO - Configuring salt minions
2021-01-06 17:31:25,733 - INFO - Configuring salt-masters
2021-01-06 17:31:36,958 - INFO - Copying factory data
2021-01-06 17:31:41,115 - INFO - Installing provisioner API
2021-01-06 17:31:52,633 - INFO - Starting salt minions
2021-01-06 17:31:56,624 - INFO - Ensuring salt-masters are ready
2021-01-06 17:32:00,314 - INFO - Ensuring salt minions are ready
2021-01-06 17:32:03,102 - INFO - Updating release distribution type
2021-01-06 17:32:05,691 - INFO - Updating target build pillar
2021-01-06 17:32:08,174 - INFO - Generating a password for the service user
2021-01-06 17:32:10,663 - INFO - Get release factory version
2021-01-06 17:32:12,043 - INFO - Sync salt modules
2021-01-06 17:32:18,035 - INFO - Configuring provisioner logging
2021-01-06 17:53:25,404 - INFO - Updating BMC IPs
2021-01-06 17:53:28,813 - INFO - Configuring setup using config.ini
2021-01-06 17:53:49,842 - INFO - Deployment on vm
2021-01-06 17:53:57,225 - INFO - Updating Salt data
2021-01-06 17:53:57,225 - INFO - Syncing states
2021-01-06 17:53:58,248 - INFO - Refreshing pillars
2021-01-06 17:53:58,701 - INFO - Refreshing grains
2021-01-06 17:53:59,215 - INFO - Applying 'components.system' on srvnode-1
2021-01-06 17:55:10,038 - INFO - Applying 'components.system.storage' on srvnode-1
2021-01-06 17:55:47,319 - INFO - Applying 'components.system.network' on srvnode-1
2021-01-06 17:56:46,595 - INFO - Applying 'components.system.network.data.public' on srvnode-1
2021-01-06 17:57:04,340 - INFO - Applying 'components.system.network.data.direct' on srvnode-1
2021-01-06 17:57:09,368 - INFO - Applying 'components.misc_pkgs.rsyslog' on srvnode-1
2021-01-06 17:57:21,226 - INFO - Applying 'components.system.firewall' on srvnode-1
2021-01-06 18:00:32,051 - INFO - Applying 'components.system.logrotate' on srvnode-1
2021-01-06 18:00:37,288 - INFO - Applying 'components.system.chrony' on srvnode-1
2021-01-06 18:00:41,090 - INFO - Applying 'components.misc_pkgs.ssl_certs' on srvnode-1
2021-01-06 18:01:25,461 - INFO - Applying 'components.ha.haproxy' on srvnode-1
2021-01-06 18:02:27,999 - INFO - Applying 'components.ha.haproxy.start' on srvnode-1
2021-01-06 18:02:31,623 - INFO - Applying 'components.misc_pkgs.openldap' on srvnode-1
2021-01-06 18:03:15,843 - INFO - Applying 'components.misc_pkgs.rabbitmq' on srvnode-1
2021-01-06 18:04:22,999 - INFO - Applying 'components.misc_pkgs.nodejs' on srvnode-1
2021-01-06 18:04:28,748 - INFO - Applying 'components.misc_pkgs.elasticsearch' on srvnode-1
2021-01-06 18:05:09,455 - INFO - Applying 'components.misc_pkgs.kibana' on srvnode-1
2021-01-06 18:05:32,688 - INFO - Applying 'components.misc_pkgs.statsd' on srvnode-1
2021-01-06 18:05:49,389 - INFO - Applying 'components.misc_pkgs.consul.install' on srvnode-1
2021-01-06 18:06:02,276 - INFO - Applying 'components.misc_pkgs.lustre' on srvnode-1
2021-01-06 18:11:20,288 - INFO - Applying 'components.motr' on srvnode-1
2021-01-06 18:12:15,381 - INFO - Applying 'components.s3server' on srvnode-1
2021-01-06 18:13:28,022 - INFO - Applying 'components.hare' on srvnode-1
2021-01-06 18:13:50,587 - INFO - Bootstraping cluster
2021-01-06 18:16:30,122 - INFO - Applying 'components.sspl' on srvnode-1
2021-01-06 18:18:19,473 - INFO - Applying 'components.uds' on srvnode-1
2021-01-06 18:18:35,498 - INFO - Applying 'components.csm' on srvnode-1
2021-01-06 18:20:00,371 - INFO - Deploy VM - Done
2021-01-06 18:20:00,371 - INFO - Done
```

- Provide the above generated log file as first argument and a csv file as second argument to the script.**  

```sh
$ python deployment_time_profiling.py deploy_log profile-report.csv
Components                                                                                           | Time taken in seconds
-----------------------------------------------------------------------------------------------------------------------------
Setup provisioner                                                                                    | 0.002
-----------------------------------------------------------------------------------------------------------------------------
Starting to build setup 'srvnode-1_root@ssc-vm-c-1810.colo.seagate.com_22'                           | 0.004
-----------------------------------------------------------------------------------------------------------------------------
Profile location '/root/.provisioner/srvnode-1_root@ssc-vm-c-1810.colo.seagate.com_22'               | 0.0
-----------------------------------------------------------------------------------------------------------------------------
Preparing setup pillar                                                                               | 0.003
-----------------------------------------------------------------------------------------------------------------------------
Generating setup keys                                                                                | 0.315
-----------------------------------------------------------------------------------------------------------------------------
Generating a roster file                                                                             | 0.001
-----------------------------------------------------------------------------------------------------------------------------
Copying config.ini to file root                                                                      | 0.005
-----------------------------------------------------------------------------------------------------------------------------
Preparing CORTX repos pillar                                                                         | 0.024
-----------------------------------------------------------------------------------------------------------------------------
Ensuring 'srvnode-1' is ready to accept commands                                                     | 10.419
-----------------------------------------------------------------------------------------------------------------------------
Resolving node grains                                                                                | 3.878
-----------------------------------------------------------------------------------------------------------------------------
Preparing salt-masters / minions configuration                                                       | 6.237
-----------------------------------------------------------------------------------------------------------------------------
srvnode-1 is reachable from other nodes by: {'192.168.31.237', 'ssc-vm-c-1810.colo.seagate.com', '10.230.240.251', '192.168.12.71', 'ssc-vm-c-1810'} | 0.002
-----------------------------------------------------------------------------------------------------------------------------
salt-masters would be set as follows: {'srvnode-1': ['127.0.0.1']}                                   | 3.002
-----------------------------------------------------------------------------------------------------------------------------
Preparing factory profile                                                                            | 0.042
-----------------------------------------------------------------------------------------------------------------------------
Installing Cortx yum repositories                                                                    | 7.892
-----------------------------------------------------------------------------------------------------------------------------
Setting up custom python repository                                                                  | 3.381
-----------------------------------------------------------------------------------------------------------------------------
Checking paswordless ssh                                                                             | 3.383
-----------------------------------------------------------------------------------------------------------------------------
Configuring the firewall                                                                             | 3.581
-----------------------------------------------------------------------------------------------------------------------------
Installing SaltStack                                                                                 | 24.363
-----------------------------------------------------------------------------------------------------------------------------
Installing provisioner from a 'rpm' source                                                           | 11.235
-----------------------------------------------------------------------------------------------------------------------------
Configuring salt minions                                                                             | 4.389
-----------------------------------------------------------------------------------------------------------------------------
Configuring salt-masters                                                                             | 11.225
-----------------------------------------------------------------------------------------------------------------------------
Copying factory data                                                                                 | 4.157
-----------------------------------------------------------------------------------------------------------------------------
Installing provisioner API                                                                           | 11.518
-----------------------------------------------------------------------------------------------------------------------------
Starting salt minions                                                                                | 3.991
-----------------------------------------------------------------------------------------------------------------------------
Ensuring salt-masters are ready                                                                      | 3.69
-----------------------------------------------------------------------------------------------------------------------------
Ensuring salt minions are ready                                                                      | 2.788
-----------------------------------------------------------------------------------------------------------------------------
Updating release distribution type                                                                   | 2.589
-----------------------------------------------------------------------------------------------------------------------------
Updating target build pillar                                                                         | 2.483
-----------------------------------------------------------------------------------------------------------------------------
Generating a password for the service user                                                           | 2.489
-----------------------------------------------------------------------------------------------------------------------------
Get release factory version                                                                          | 1.38
-----------------------------------------------------------------------------------------------------------------------------
Sync salt modules                                                                                    | 5.992
-----------------------------------------------------------------------------------------------------------------------------
Configuring provisioner logging                                                                      | 1267.369
-----------------------------------------------------------------------------------------------------------------------------
Updating BMC IPs                                                                                     | 3.409
-----------------------------------------------------------------------------------------------------------------------------
Configuring setup using config.ini                                                                   | 21.029
-----------------------------------------------------------------------------------------------------------------------------
Deployment on vm                                                                                     | 7.383
-----------------------------------------------------------------------------------------------------------------------------
Updating Salt data                                                                                   | 0.0
-----------------------------------------------------------------------------------------------------------------------------
Syncing states                                                                                       | 1.023
-----------------------------------------------------------------------------------------------------------------------------
Refreshing pillars                                                                                   | 0.453
-----------------------------------------------------------------------------------------------------------------------------
Refreshing grains                                                                                    | 0.514
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.system' on srvnode-1                                                            | 70.823
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.system.storage' on srvnode-1                                                    | 37.281
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.system.network' on srvnode-1                                                    | 59.276
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.system.network.data.public' on srvnode-1                                        | 17.745
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.system.network.data.direct' on srvnode-1                                        | 5.028
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.rsyslog' on srvnode-1                                                 | 11.858
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.system.firewall' on srvnode-1                                                   | 190.825
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.system.logrotate' on srvnode-1                                                  | 5.237
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.system.chrony' on srvnode-1                                                     | 3.802
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.ssl_certs' on srvnode-1                                               | 44.371
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.ha.haproxy' on srvnode-1                                                        | 62.538
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.ha.haproxy.start' on srvnode-1                                                  | 3.624
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.openldap' on srvnode-1                                                | 44.22
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.rabbitmq' on srvnode-1                                                | 67.156
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.nodejs' on srvnode-1                                                  | 5.749
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.elasticsearch' on srvnode-1                                           | 40.707
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.kibana' on srvnode-1                                                  | 23.233
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.statsd' on srvnode-1                                                  | 16.701
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.consul.install' on srvnode-1                                          | 12.887
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.misc_pkgs.lustre' on srvnode-1                                                  | 318.012
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.motr' on srvnode-1                                                              | 55.093
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.s3server' on srvnode-1                                                          | 72.641
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.hare' on srvnode-1                                                              | 22.565
-----------------------------------------------------------------------------------------------------------------------------
Bootstraping cluster                                                                                 | 159.535
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.sspl' on srvnode-1                                                              | 109.351
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.uds' on srvnode-1                                                               | 16.025
-----------------------------------------------------------------------------------------------------------------------------
Applying 'components.csm' on srvnode-1                                                               | 84.873
-----------------------------------------------------------------------------------------------------------------------------
Deploy VM - Done                                                                                     | 0.0
-----------------------------------------------------------------------------------------------------------------------------
CSV report saved in  profile-report.csv file
```

- Output is saved in `profile-report.csv` file in CSV format.**
