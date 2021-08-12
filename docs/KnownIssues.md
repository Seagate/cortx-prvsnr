# Known deployment issues


## Known Issue 1: aws s3 ls fails as openldap database does not sync across the nodes

**Problem:**  
  [EOS-6598](https://jts.seagate.com/browse/EOS-6598) aws s3 ls fails as openldap database does not sync across the nodes  
  

**Description:**  
  Openldap ports need to be opened in the firewall.

  ```
  [root@smc26-m10 .aws]# aws s3 ls
  2020-03-30 04:36:33 seagatebucket
  [root@smc26-m10 .aws]# aws s3 lsAn error occurred (InvalidAccessKeyId) when calling the ListBuckets operation: The 
  AWS access key Id you provided does not exist in our records.
  [root@smc26-m10 .aws]#
  ``` 

**Solution:**  
  Until the fix is provided user following workaround:
  ```
  Run these from primary node

  # salt ‘*’ cmd.run “firewall-cmd --zone=public --permanent --add-port=389/tcp”
  # salt ‘*’ service.restart firewalld
  # ssh eosnode-2 “systemctl restart salt-minion”
  # salt ‘*’ test.ping
  # salt ‘*’ service.restart slapd 
  ```

## Known Issue 2: At the end of setup-provisioner, the command appears hung while updating the salt mines

**Problem:**  
   At the end of setup-provisioner, the command appears hung while updating the salt mines.  
   The command will hung like this:  
   ```
   INFO: Updating hostnames in cluster pillar
   INFO: Updating target build in release pillar
   INFO: Triggering salt data mining
   eosnode-1:
       True
   ```
**Solution:**
   Just terminate the command using ctrl+c to end it.
   Ensure that salt configuration is working fine:
   ```
   # salt '*' test.ping
   eosnode-1:
       True
   eosnode-2:
       True
   ```
   Should return True for both the nodes

**Issue status:** PRESUMABLY RESOLVED. Upd. from 2020-04-21  

## Known Issue 3: s3 endpoints points to wrong ip in */etc/hosts*
**Problem:**  
  s3 endpoints points to wrong ip in */etc/hosts*

**Description:**
  After cluster ip feature is added, the s3 endpoints (*s3.seagate sts.seagate.com iam.seagate.com 
  sts.cloud.seagate.com*) need to point to cluster ip on both the nodes but they point to data interface ip.  

**Solution:**  
 **Update */etc/hosts* file on both nodes** so that all s3 endpoints point to the cluster ip.  
 Run following command **on primary node** to get the cluster ip:  
 ```
 $ salt 'eosnode-1' pillar.item cluster:cluster_ip | tail -1
   172.19.222.27
 ```
 put this cluster ip in */etc/hosts* against s3 endpoints  
 ``` 
 $ cat /etc/hosts | grep s3
 172.19.222.27  s3.seagate.com sts.seagate.com iam.seagate.com   sts.cloud.seagate.com
 ``` 
**NOTE:** The above line will already be there in */etc/hosts* just update it with cluster ip.

## Known Issue 4: `pcs status` shows some services under *Failed Resource Action*
**Problem:**  
  `pcs status` shows some services under *Failed Resource Action*

**Description:**
  After the cluster is deployed successfully and all the eos services are listed as 'started' a few services are listed uneder "Failed Resource Action"

**Solution:**  
  They are harmless for now and they will get removed as part of HA milestone 3 (M3).

**Issue status:** RESOLVED. Upd. from 2020-04-21  

## Known Issue 5: deploy-eos fails during provisioning of HA component.
**Problem:**  
 deploy-eos fails during provisioning of HA component.

**Description:**
  deploy-eos fails with following error:  
  ```
  ----------
  ID: start IOStack HA cluster
    Function: cmd.run
    Name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:init')
    Result: False
    Comment: Command "/opt/seagate/eos/hare/libexec/build-ha /var/lib/hare/cluster.yaml /var/lib/
    hare/build-ha-args.yaml" run
    Started: 06:16:07.483593
    Duration: 8516.062 ms
    Changes:   
              ----------
              pid:
                  57761
              retcode:
                  1
              stderr:
                  ERROR: the IP address on the sm10-r20.pun.seagate.com failed to be configured.
                  Check the networking configuration, make sure the netmask of
                  the main IP on enp175s0f1 interface is <= 24 bits.
              stdout:
                  Adding the roaming IP addresses into Pacemaker...
                  Warning: Validation for node existence in the cluster will be skipped
                  Warning: Validation for node existence in the cluster will be skipped
                  CIB updated
                  Adding LNet...
                  Adding lnet-clone ip-c1 (kind: Mandatory) (Options: first-action=start then-action=$tart)
                  Adding lnet-clone ip-c2 (kind: Mandatory) (Options: first-action=start then-action=start)
                  CIB updated
                  CIB updated
                  Preparing Hare configuration files...
  ```  
  This is a config issue and finding a root cause is in progress *(XXX Jira link?)*. 
  There is a workaround available:   

**Solution:**  
  Run following commands in the exact **same sequence from primary node**:  
  ```
  pcs cluster stop --all    # This takes time, if it takes forever then kill it and run next command
  pcs cluster destroy
  salt 'eosnode-2' state.apply components.ha.corosync-pacemaker
  salt 'eosnode-1' state.apply components.ha.corosync-pacemaker
  ```
  Run following commands **on both the nodes**  
  ```
  - find out the failed services.   
    systemctl list-units --state=failed
  - reset the failed services for all failed services listed in prev command:  
    systemctl reset-failed <failed - service >
  ```
  Rerun the iostack-ha component again:  
  ```
  salt '*' state.apply components.ha.iostack-ha
  ```

**Issue status:** RESOLVED. Upd. from 2020-04-21  

## Known Issue 6: deploy-eos fails during provisioning of HA component.
**Problem:**  
 [EOS-6325](https://jts.seagate.com/browse/EOS-6325)  
 deploy-eos fails during provisioning of HA component.   

**Description:**
  deploy-eos fails with following error:  
  ```
  ----------
  ID: start IOStack HA cluster
    Function: cmd.run
    Name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:init')
    Result: False
    Comment: Command "/opt/seagate/eos/hare/libexec/build-ha /var/lib/hare/cluster.yaml /var/lib/
    hare/build-ha-args.yaml" run
    Started: 06:16:07.483593
    Duration: 8516.062 ms
    Changes:   
              ----------
              pid:
                  57761
              retcode:
                  1
              stderr:
                  ?[1;33mWarning?[0m: Could not locate a cache base directory from the environment.

                  You can provide a cache base directory by pointing the $XDG_CACHE_HOME
                  environment variable to a directory with read and write permissions.


                  ?[1;33mWarning?[0m: Could not locate a cache base directory from the environment.

                  You can provide a cache base directory by pointing the $XDG_CACHE_HOME
                  environment variable to a directory with read and write permissions.
                  
                  { Truncated output}

                  mount: special device /dev/disk/by-id/dm-name-mpathp2 does not exist
  ```  
  This is [known issue with multipath](https://access.redhat.com/solutions/227073) on Rehad based systems
  
**Solution:**  
  This will be fixed in Provisioning soon to forcefully detect the path of the multipath devices.  

  As a workaround please run following commands in the exact **same sequence from primary node**:  
  ```
  pcs cluster stop --all    # This takes time, it takes forever kill it and run next command
  pcs cluster destroy
  salt 'eosnode-2' state.apply components.ha.corosync-pacemaker
  salt 'eosnode-1' state.apply components.ha.corosync-pacemaker
  salt '*' state.apply components.ha.iostack-ha.teardown  
  ```
  Run following commands on both the nodes  
  - unmount /var/mero if mounted  
      $ `umount /var/mero `  
  - find out the failed services.   
      $ `systemctl list-units --state=failed`  
  - reset the failed services for all failed services listed in prev command:  
    systemctl reset-failed <failed - service >  
  
  Rerun the iostack-ha component again:  
  $ `salt '*' state.apply components.ha.iostack-ha`  

  Run deploy-eos command to continue installing the rest of the components  
  $ `sh /opt/seagate/eos-prvsnr/cli/deploy-eos -v`  

**Issue status:** ACTIVE. Reproduced during partial re-provisioning. Upd. from 2020-04-29  

## Known Issue 7: after deploy-eos is run successfuly service haproxy remains in failed state.
**Problem:**  
 after deploy-eos is run successfuly service haproxy remains in failed state.   

**Description:**
  [EOS-6369](https://jts.seagate.com/browse/EOS-6369)
  deploy-eos runs successfully but due to the issue mentioned above EOS-6369 the haproxy service remains in failed state.

**Solution:** 
  restart the haproxy service on both nodes using following command, run this on primary node:  
  $`salt '*' service.start haproxy`  

## Known Issue 8: issue is a blocker for LCO lab nodes. `cluster_ip` parameter can't be set in cluster.sls
[EOS-5922](https://jts.seagate.com/browse/EOS-5922) issue is a blocker for LCO lab nodes. `cluster_ip` parameter can't be set in cluster.sls.  
Please check status this issue before doing provisioning.

**Issue status:** RESOLVED. Upd. from 2020-04-20


## Known Issue 9: RPM or RPM dependencies fail to install.  
[Puppet periodically cleans up the repos under `/etc/yum.repo.d` directory]  
**Problem:**  Puppet periodically cleans up the repos under `/etc/yum.repo.d` directory
**Description:**  
RPM or RPM dependencies fail to install.  
E.g.
```
Error: Package: salt-2019.2.0-2.el7.noarch (saltstack)
           Requires: python36-tornado >= 4.2.1
```
This happens on the Puppet managed systems (LCO Lab nodes & SSC VMs).  
It was found that enabled puppet agent causes `/etc/yum.repo.d` directory to be cleaned at arbitrary moment during deploy.    
It leads to deploy fail when some random package can't be installed due to missing dependencies - in fact - missing repos.  

**Solution:**   
Switching to subscription manager based repos will solve it, it's in progress (EOS-7979).  
There is following workaround available for now:  
Workaround:  
Run following commands once system is successfully loaded after OS provisioning.  

$ `systemctl stop puppet.service`  
$ `systemctl disable puppet.service`  
If the repos are deleted, run following command to restore the repos:  
$ `curl http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/prvsnr_uploads/eos-install-prereqs.sh | bash -s`   

**Issue status:** ACTIVE. Upd. from 2020-04-21  

## Known Issue 10: deploy-eos fails during nodejs components  
**Problem:** deploy-eos fails during nodejs components  
**Description:**  
  The deploye-eos script fails with following error while provisioning the nodejs component:  

  ```  
  eosnode-1:
  ----------
       ID: Extract Node.js
       Function: archive.extracted
       Name: /opt/nodejs
       Result: False
       Comment: Error: HTTP 500: Internal Server Error reading http://nodejs.org/dist/v12.13.0/node-v12.13.0-linux-x64.tar.xz
       Started: 19:39:42.145335
       Duration: 1478.155 ms
       Changes:
  ----------
       ID: Check nodejs version
      Function: cmd.run
      Name: /opt/nodejs/node-v12.13.0-linux-x64/bin/node -v
      Result: False
      Comment: One or more requisite failed: components.misc_pkgs.nodejs.Extract Node.js
      Started: 19:39:43.624650
      Duration: 0.006 ms
      Changes:
  ```  
  This is not completely root caused but initial investigation suggests that it happens due to intermittent network outage.  

**Solution:**  
  Rerun the component again:  
  $ `salt '*' state.apply components.misc_pkgs.nodejs.teardown && salt '*' state.apply components.misc_pkgs.nodejs`  
  Run deploy-eos again by skipping the components provisioned so far.  

**Issue status:** PRESUMABLY RESOLVED. Upd. from 2020-04-21  

  
## Known Issue 11: deploy-eos fails to install eoscore component  
**Problem:** deploy-eos fails to install eoscore component  
**Description:**  
  deploy-eos fails to provision eoscore with cpio error:  

  ```  
  ----------
          ID: Install EOSCore
    Function: pkg.installed
      Result: False
     Comment: Error occurred installing package(s). Additional info follows:
              errors:
                  - Running scope as unit run-95141.scope.
                    Loaded plugins: enabled_repos_upload, package_upload, product-id, search-
                                  : disabled-repos, subscription-manager
                    This system is not registered with an entitlement server. You can use subscription-manager to register.
                    Resolving Dependencies
                    --> Running transaction check
                    ---> Package eos-core.x86_64 0:1.0.0-224_git71cd330a1_3.10.0_1062.el7 will be installed
                    --> Finished Dependency Resolution
                    Dependencies Resolved
                    ================================================================================
                     Package    Arch     Version                                    Repository
                                                                                               Size
                    ================================================================================
                    Installing:
                     eos-core   x86_64   1.0.0-224_git71cd330a1_3.10.0_1062.el7     eoscore    28 M
                    Transaction Summary
                    ================================================================================
                    Install  1 Package
                    Total download size: 28 M
                    Installed size: 141 M
                    Downloading packages:
                    Running transaction check
                    Running transaction test
                    Transaction test succeeded
                    Running transaction
                      Installing : eos-core-1.0.0-224_git71cd330a1_3.10.0_1062.el7.x86_64       1/1Error unpacking rpm package eos-core-1.0.0-224_git71cd330a1_3.10.0_1062.el7.x86_64
                    error: unpacking of archive failed on file /usr/libexec/mero: cpio: rename
                    Uploading Package Profile
                      Verifying  : eos-core-1.0.0-224_git71cd330a1_3.10.0_1062.el7.x86_64       1/1
                    Failed:
                      eos-core.x86_64 0:1.0.0-224_git71cd330a1_3.10.0_1062.el7
                    Complete!
                    Uploading Enabled Repositories Report
     Started: 14:10:33.628967
    Duration: 19456.695 ms
     Changes:
  ----------  
  ```  
  The error is because the rpm name of mero got changed to eos-core from build #1436.
  This occurs if the system is not freshly re-imaged.
  
**Solution:**  
  Delete the following file and retry again, following command does the same:  
  $ `salt '*' cmd.run "rm -rf /usr/libexec/mero*" && ./deploy-eos --iopath-states --ha-states --ctrlpath-states` 

**Issue status:** PRESUMABLY RESOLVED. Upd. from 2020-04-21  


## Known Issue 12: deploy-eos fails to provision iostack-ha component  
**Problem:** deploy-eos fails to provision iostack-ha component    
**Description:**  
  deploy-eos fails to provision iostack-ha component and errors out with following error  
  ```
  ----------
          ID: start IOStack HA cluster
    Function: cmd.run
        Name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:init')
      Result: False
     Comment: Command "/opt/seagate/eos/hare/libexec/build-ha /var/lib/hare/cluster.yaml /var/lib/hare/build-ha-args.yaml" run
     Started: 13:40:15.729859
    Duration: 14.716 ms
     Changes:   
              ----------
              pid:
                  65391
              retcode:
                  1
              stderr:
                  build-ha: ERROR: meta-data volume /dev/disk/by-id/dm-name-mpatho2 is not available
              stdout:
  ```  
**Solution:**  
  On some systems it is observed that the partitions are not getting updated across nodes  
  Update the partition using parprobe and retry:  
  $ `salt '*' cmd.run "partprobe /dev/disk/by-id/dm-name-mpath*"`  
  $ `salt '*' state.apply components.ha.iostack-ha.teardown && salt '*' state.apply components.ha.iostack-ha`  
  To continue with sspl and csm components run deploy-eos again:  
  $ `deploy-eos --ctrlpath-states`  

## Known Issue 13: deploy-eos fails to provision post_setup component with build#1507  
**Problem:** deploy-eos fails to provision post_setup component with build#1507     
**Description:**  
  post_setup component fails during deploy-eos with following error:  
  ```
  INFO: Applying 'components.post_setup' for both nodes
eosnode-2:
----------
          ID: Post install for SSPL
    Function: cmd.run
        Name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/sspl/conf/setup.yaml', 'sspl:ha')
      Result: False
     Comment: Command "/opt/seagate/eos/hare/libexec/build-ha-sspl /var/lib/hare/build-ha-args.yaml" run
     Started: 06:20:54.631085
    Duration: 28.53 ms
     Changes:   
              ----------
              pid:
                  92539
              retcode:
                  1
              stderr:
                  [sm21-r22.pun.seagate.com] build-ha-sspl: No active Consul instance found
              stdout:
----------
          ID: Post install for CSM
    Function: cmd.run
        Name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/csm/conf/setup.yaml', 'csm:ha')
      Result: False
     Comment: Command "/opt/seagate/eos/hare/libexec/build-ha-csm /var/lib/hare/build-ha-csm-args.yaml" run
     Started: 06:20:54.659825
    Duration: 23.967 ms
     Changes:   
              ----------
              pid:
                  92544
              retcode:
                  1
              stderr:
                  [sm21-r22.pun.seagate.com] build-ha-csm: No active Consul instance found
              stdout:

Summary for eosnode-2
------------
Succeeded: 0 (changed=2)
Failed:    2
------------
  ```  
**Solution:**  
  It is safe to ignore it.  
  Just ensure that the `pcs status` is showing all services as started.  

## Known Issue 14: deploy-eos fails to provision iostack-ha  
**Problem:** deploy-eos fails to provision iostack-ha.     
**Description:**  
This is not a bug, but cleanup issue. iostack-ha don't clean up hare-consul-agent during teardown  
  ```
         ID: start IOStack HA cluster
    Function: cmd.run
        Name: __slot__:salt:setup_conf.conf_cmd('/opt/seagate/eos/hare/conf/setup-ha.yaml', 'hare:init')
      Result: False
     Comment: Command "/opt/seagate/eos/hare/libexec/build-ha /var/lib/hare/cluster.yaml /var/lib/hare/build-ha-args.yaml" run
     Started: 05:48:51.207723
    Duration: 9916.546 ms
     Changes:
              ----------
              pid:
                  174010
              retcode:
                  1
              stderr:
                  hare-bootstrap: hare-consul-agent is active ==> cluster is already running
              stdout:
                  Adding the roaming IP addresses into Pacemaker...
                  Warning: Validation for node existence in the cluster will be skipped
                  Warning: Validation for node existence in the cluster will be skipped
                  CIB updated
                  Adding LNet...
                  Adding lnet-clone ip-c1 (kind: Mandatory) (Options: first-action=start then-action=start)
                  Adding lnet-clone ip-c2 (kind: Mandatory) (Options: first-action=start then-action=start)
                  CIB updated
                  CIB updated
                  Preparing Hare configuration files...
 
  ```  
**Solution:**  
  clean up the service - hare-consul-agent on both nodes, teardown iostack-ha and rerun it again.  
   $ `salt '*' service.stop hare-consul-agent`  
   $ `salt '*' state.apply components.ha.iostack-ha.teardown`  
   $ `salt '*' state.apply components.ha.iostack-ha`  

## Known Issue 15: deploy-eos fails to provision openldap on eosnode-2
**Problem:** deploy-eos fails to provision openldap on eosnode-2  
**Description:**  
Root cause of below issue is cluster_id miss-match across nodes:  
```
[INFO    Apr 15 04:47 ]: Applying 'components.misc_pkgs.openldap' for eosnode-2                                                                                    [98/1906]
eosnode-2:
    Data failed to compile:
----------
    Rendering SLS 'base:components.misc_pkgs.openldap.config.base' failed: Jinja error: Decryption failed
Traceback (most recent call last):
  File "/usr/lib64/python3.6/site-packages/cryptography/fernet.py", line 104, in _verify_signature
    h.verify(data[-32:])
  File "/usr/lib64/python3.6/site-packages/cryptography/hazmat/primitives/hmac.py", line 66, in verify
    ctx.verify(signature)
  File "/usr/lib64/python3.6/site-packages/cryptography/hazmat/backends/openssl/hmac.py", line 74, in verify
    raise InvalidSignature("Signature did not match digest.")
cryptography.exceptions.InvalidSignature: Signature did not match digest.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3.6/site-packages/eos/utils/security/cipher.py", line 49, in decrypt
    decrypted = Fernet(key).decrypt(data)
  File "/usr/lib64/python3.6/site-packages/cryptography/fernet.py", line 75, in decrypt
    return self._decrypt_data(data, timestamp, ttl)
  File "/usr/lib64/python3.6/site-packages/cryptography/fernet.py", line 117, in _decrypt_data
    self._verify_signature(data)
  File "/usr/lib64/python3.6/site-packages/cryptography/fernet.py", line 106, in _verify_signature
    raise InvalidToken
cryptography.fernet.InvalidToken

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/lib/python3.6/site-packages/salt/utils/templates.py", line 392, in render_jinja_tmpl
    output = template.render(**decoded_context)
  File "/usr/lib/python3.6/site-packages/jinja2/environment.py", line 989, in render
    return self.environment.handle_exception(exc_info, True)
  File "/usr/lib/python3.6/site-packages/jinja2/environment.py", line 754, in handle_exception
    reraise(exc_type, exc_value, tb)
  File "/usr/lib/python3.6/site-packages/jinja2/_compat.py", line 37, in reraise
    raise value.with_traceback(tb)
  File "<template>", line 3, in top-level template code
  File "/var/cache/salt/minion/extmods/modules/lyveutil.py", line 20, in decrypt
    retval = (Cipher.decrypt(cipher_key, secret.encode("utf-8"))).decode("utf-8")
  File "/usr/lib/python3.6/site-packages/eos/utils/security/cipher.py", line 51, in decrypt
    raise CipherInvalidToken(f'Decryption failed')
eos.utils.security.cipher.CipherInvalidToken: Decryption failed

; line 3
```  
**Cause:**  
```
$ salt "*" grains.get cluster_id
eosnode-1:
    1fc03122-d7d4-4ee4-849a-cf0a1709f46a
eosnode-2:
    eb21357f-41eb-4a7b-b94e-0c48e51cbfd5
```  
**Solution:**  
```
# Fix
$ cluster_id_var=$(salt-call grains.get cluster_id --output=newline_values_only);ssh eosnode-2 "sed -i 's/cluster_id:.*/cluster_id: ${cluster_id_var}/g' /etc/salt/grains"; salt "*" saltutil.refresh_grains
eosnode-1:
    True
eosnode-2:
    True

# Confirm
$ salt "*" grains.get cluster_id
eosnode-1:
    1fc03122-d7d4-4ee4-849a-cf0a1709f46a
eosnode-2:
    1fc03122-d7d4-4ee4-849a-cf0a1709f46a

# Reset Openldap
$ salt "*" state.apply components.misc_pkgs.openldap.teardown

# Resume Provisioner
$ sh /opt/seagate/eos-prvsnr/cli/deploy-eos
```

## Known Issue 16: auto-deploy-eos remains hung while updating salt metadata   
**Problem:** auto-deploy-eos remains hung while updating salt data  

**Description:**  
The command appears hung after following message:  
```
***** INFO: Running deploy-eos *****  
Updating Salt data  
```  
The root cause is unknown.  

**Solution:**   
This hang situation is at the start of the deploy-eos command.  
Solution is to run the deploy-eos command manually.  

## Known Issue 17: deploy-eos fails during storage component while make/enable swap partition  
**Problem:** deploy-eos fails during storage component while make/enable swap partition    
**Description:**  
Open the deploy log and check if there are any error related to swap:  
```
118678 ----------
118679           ID: Make SWAP partition
118680     Function: cmd.run
118681         Name: mkswap -f /dev/disk/by-id/dm-name-mpatho4 && sleep 5
118682       Result: False
118683      Comment: Command "mkswap -f /dev/disk/by-id/dm-name-mpatho4 && sleep 5" run
118684      Started: 06:30:15.836772
118685     Duration: 11.086 ms
118686      Changes:
118687               ----------
118688               pid:
118689                   249129
118690               retcode:
118691                   1
118692               stderr:
118693                   /dev/disk/by-id/dm-name-mpatho4: Device or resource busy
118694               stdout:
118695 ----------
118696           ID: Enable swap
118697     Function: mount.swap
118698         Name: /dev/disk/by-id/dm-name-mpatho4
118699       Result: False
118700      Comment: One or more requisite failed: components.system.storage.config.Make SWAP partition
118701      Started: 06:30:15.849606
118702     Duration: 0.003 ms
118703      Changes:
118704 ----------

```  
The root cause is unknown as of now, but mostly it's due to the timing issue.  

**Solution:**   
Even after the above error in log file the swap gets enabled most of the time. Check if the swap is enabled, if so, rerun the deploy-eos command.  
Check what is the metadata device:
```
[root@smc39-m09 ~]# grep -A1 metadata /opt/seagate/eos-prvsnr/pillar/user/groups/all/cluster.sls
            metadata_devices:
            - /dev/disk/by-id/dm-name-mpatho
--
            metadata_devices:
            - /dev/disk/by-id/dm-name-mpatha
```  
Check if SWAP is mounted on these devices  
```
[root@smc39-m09 ~]# lsblk | grep SWAP
  ├─mpatho4              253:13   0   7.8T  0 part  [SWAP]
  ├─mpatho4              253:13   0   7.8T  0 part  [SWAP]
[root@smc39-m09 ~]# ssh srvnode-2 "lsblk | grep SWAP"
  ├─mpatha4              253:17   0   7.8T  0 part  [SWAP]
  ├─mpatha4              253:17   0   7.8T  0 part  [SWAP]
[root@smc39-m09 ~]# 

```
So, if swap is mounted on the metadata device partition, you can safely ignore this error and run:  
$ `deploy-eos`  

## Known Issue 18: deploy-eos fails for openldap deployment for ldap_add     
**Problem:** auto-deploy-eos/deploy-eos command fails during openldap    
```
ldap_add: Other (e.g., implementation specific) error (80)
                        additional info: <olcModuleLoad> handler exited with 1
```
**Description:**  

The openldap component fails, this typically happens if the setup is previously teared down.  
The deploy-eos logs shows following error:  
   
```
----------
          ID: Configure openldap syncprov_mod
    Function: cmd.run
        Name: ldapadd -Y EXTERNAL -H ldapi:/// -f /opt/seagate/eos-prvsnr/generated_configs/ldap/syncprov_mod.ldif
      Result: False
     Comment: Command "ldapadd -Y EXTERNAL -H ldapi:/// -f /opt/seagate/eos-prvsnr/generated_configs/ldap/syncprov_mod.ldif" run
     Started: 02:40:20.261706
    Duration: 15.513 ms
     Changes:
              ----------
              pid:
                  26464
              retcode:
                  80
              stderr:
                  SASL/EXTERNAL authentication started
                  SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
                  SASL SSF: 0
                  ldap_add: Other (e.g., implementation specific) error (80)
                        additional info: <olcModuleLoad> handler exited with 1
              stdout:
                  adding new entry "cn=module,cn=config"
----------
```
**Solution:**   
Teardown the openldap and run deploy-eos again.  
$ `salt '*' state.apply components.misc_pkgs.openldap.teardown`  
$ `sh /opt/seagate/eos-prvnsr/cli/deploy-eos`  


**If OpenLDAP hangs**  
**Solution:**
```
Kill the process and follow the below steps:  
     salt "*" saltutil.kill_all_jobs
     salt "*" state.apply components.misc_pkgs.openldap.teardown
     /opt/seagate/cortx/provisioner/cli/deploy
```

## Known Issue 19: LVM issue - auto-deploy fails during provisioning of storage component ([EOS-12289](https://jts.seagate.com/browse/EOS-12289)).     

**Problem:** auto-deploy/deploy command fails during provisioning of components.system.storage    

**Description:**  
Even after fresh OS install (re-image) the `lsblk` lists volumes with LVM configuration from previous deploy as shown below:

```
[root@smcxx-mxx ~]# lsblk | grep "vg_metadata_srvnode--2-lv_main_swap"
    ├─vg_metadata_srvnode--2-lv_main_swap    253:28   0  29.2T  0 lvm   
    ├─vg_metadata_srvnode--2-lv_main_swap    253:28   0  29.2T  0 lvm   
[root@smcxx-mxx ~]# 

```

**Solution:**   
The metadata of LVM partitions created on metadata volumes is stored on the volume itself, so even if the OS is reinstalled if the LVM data is not removed from the volume it would appear again when the same volumes from storage enclosure are used from previous deployment. 

The solution is to cleanup/teardown the LVM configuration before reinstalling the OS.
Please follow the following steps until the way to fix this in Provisioner is identified.

1. Run following storage teardown command before reimage:
   `salt '*' state.apply components.system.storage.teardown`
2. Unmap the volumes from storage enclosure
3. Re-image the node(s)
4. Reconfigure the volumes (Optional) and map them to all the initiators
5. Before starting the autodeploy check 'lsblk -S | grep sas' and ensure that it matches with the volumes.
6. run `lsblk` to check if previous LVM partitions are seen (If yes, don't proceed and contact Provisioning team else proceed to the next step, )
7. Run auto-deploy

### Manual Fix in case the node has been reimaged
1.  Remove volume_groups, if present  
    ```
    swapoff -a
    for vggroup in $(vgdisplay | grep vg_metadata_srvnode-|tr -s ' '|cut -d' ' -f 4); do
        echo "Removing volume group ${vggroup}"
        vgremove --force ${vggroup}
    done
    ```
    **Note**: The above automation carries out the following steps:  
    1.  To check presense of vgroup  
        ```
        vgdisplay | grep vg_metadata_srvnode-|tr -s ' '|cut -d' ' -f 4
        ```   
    1.  Remove vgroup for srvnode-1  
        ```
        [root@smc49-m08 ~]# (vgdisplay | grep vg_metadata_srvnode-1) && vgremove vg_metadata_srvnode-1 --force
          WARNING: Not using lvmetad because duplicate PVs were found.
          WARNING: Use multipath or vgimportclone to resolve duplicate PVs?
          WARNING: After duplicates are resolved, run "pvscan --cache" to enable lvmetad.
          WARNING: Not using device /dev/sdr2 for PV H6OE0a-kcpF-jvvb-ddO1-CSqN-0c0d-RTIn6p.
          WARNING: Not using device /dev/sdz2 for PV fiSRUo-iIVs-Hhuw-Xp8n-u1A9-2h1t-CvUTdH.
          WARNING: PV H6OE0a-kcpF-jvvb-ddO1-CSqN-0c0d-RTIn6p prefers device /dev/sdb2 because device is used by LV.
          WARNING: PV fiSRUo-iIVs-Hhuw-Xp8n-u1A9-2h1t-CvUTdH prefers device /dev/sdj2 because device was seen first.
          VG Name               vg_metadata_srvnode-1
          WARNING: Not using lvmetad because duplicate PVs were found.
          WARNING: Use multipath or vgimportclone to resolve duplicate PVs?
          WARNING: After duplicates are resolved, run "pvscan --cache" to enable lvmetad.
          WARNING: Not using device /dev/sdr2 for PV H6OE0a-kcpF-jvvb-ddO1-CSqN-0c0d-RTIn6p.
          WARNING: Not using device /dev/sdz2 for PV fiSRUo-iIVs-Hhuw-Xp8n-u1A9-2h1t-CvUTdH.
          WARNING: PV H6OE0a-kcpF-jvvb-ddO1-CSqN-0c0d-RTIn6p prefers device /dev/sdb2 because device is used by LV.
          WARNING: PV fiSRUo-iIVs-Hhuw-Xp8n-u1A9-2h1t-CvUTdH prefers device /dev/sdj2 because device was seen first.
          Logical volume "lv_main_swap" successfully removed
          Logical volume "lv_raw_metadata" successfully removed
          Volume group "vg_metadata_srvnode-1" successfully removed  
        ```
    1.  Remove vgroup for srvnode-2  
        ```
        [root@smc49-m08 ~]# (vgdisplay | grep vg_metadata_srvnode-2) && vgremove vg_metadata_srvnode-2 --force
          WARNING: Not using lvmetad because duplicate PVs were found.
          WARNING: Use multipath or vgimportclone to resolve duplicate PVs?
          WARNING: After duplicates are resolved, run "pvscan --cache" to enable lvmetad.
          WARNING: Not using device /dev/sdr2 for PV H6OE0a-kcpF-jvvb-ddO1-CSqN-0c0d-RTIn6p.
          WARNING: Not using device /dev/sdz2 for PV fiSRUo-iIVs-Hhuw-Xp8n-u1A9-2h1t-CvUTdH.
          WARNING: PV H6OE0a-kcpF-jvvb-ddO1-CSqN-0c0d-RTIn6p prefers device /dev/sdb2 because device was seen first.
          WARNING: PV fiSRUo-iIVs-Hhuw-Xp8n-u1A9-2h1t-CvUTdH prefers device /dev/sdj2 because device was seen first.
          VG Name               vg_metadata_srvnode-2
          WARNING: Not using lvmetad because duplicate PVs were found.
          WARNING: Use multipath or vgimportclone to resolve duplicate PVs?
          WARNING: After duplicates are resolved, run "pvscan --cache" to enable lvmetad.
          WARNING: Not using device /dev/sdr2 for PV H6OE0a-kcpF-jvvb-ddO1-CSqN-0c0d-RTIn6p.
          WARNING: Not using device /dev/sdz2 for PV fiSRUo-iIVs-Hhuw-Xp8n-u1A9-2h1t-CvUTdH.
          WARNING: PV H6OE0a-kcpF-jvvb-ddO1-CSqN-0c0d-RTIn6p prefers device /dev/sdb2 because device was seen first.
          WARNING: PV fiSRUo-iIVs-Hhuw-Xp8n-u1A9-2h1t-CvUTdH prefers device /dev/sdj2 because device was seen first.
          Logical volume "lv_main_swap" successfully removed
          Logical volume "lv_raw_metadata" successfully removed
          Volume group "vg_metadata_srvnode-2" successfully removed  
        ```  

1.  Remove partitions from volumes  
    ```
    partprobe
    for partition in $( ls -1 /dev/disk/by-id/scsi-*|grep part1|cut -d- -f3 ); do
        if parted /dev/disk/by-id/scsi-${partition} print; then 
            echo "Removing partition 2 from /dev/disk/by-id/scsi-${partition}"
            parted /dev/disk/by-id/scsi-${partition} rm 2
            echo "Removing partition 1 from /dev/disk/by-id/scsi-${partition}"
            parted /dev/disk/by-id/scsi-${partition} rm 1
        fi
    done
    partprobe
    ```  
    **NOTE**: The above is automation for the following 4 steps:  
    1.  Use command to identify the partitioned volumes (in absense of mpath configuration):
        ```  
        [root@smc50-m08 ~]# ls -1 /dev/disk/by-id/scsi-*  
        ```  
    1.  Look for volumes with extention -part1 and -part2  
        Select it's parent volume  
        E.g. in command output below, select the first entry  
        ```  
        /dev/disk/by-id/scsi-3600c0ff00050efcdddc4ab5e01000000
        /dev/disk/by-id/scsi-3600c0ff00050efcdddc4ab5e01000000-part1
        /dev/disk/by-id/scsi-3600c0ff00050efcdddc4ab5e01000000-part2
        ```  
    1.  Ensure this volume is partitioned using command  
        E.g.  
        ```
        [root@smc50-m08 ~]# parted /dev/disk/by-id/scsi-3600c0ff00050efcdddc4ab5e01000000 print
        Model: SEAGATE 5565 (scsi)
        Disk /dev/sdb: 63.9TB
        Sector size (logical/physical): 512B/4096B
        Partition Table: gpt
        Disk Flags:
        Number  Start   End     Size    File system  Name     Flags
        1      1049kB  1000GB  1000GB  ext4         primary
        2      1001GB  63.9TB  62.9TB               primary  lvm
        ```  
    1.  Once confirmed, remove the partitions on the identified volume  
        E.g.  
        ```
        [root@smc50-m08 ~]# parted /dev/disk/by-id/scsi-3600c0ff00050efcdddc4ab5e01000000 rm 2
        [root@smc50-m08 ~]# parted /dev/disk/by-id/scsi-3600c0ff00050efcdddc4ab5e01000000 rm 1
        ```  
        Run partprobe on both nodes to refresh the listing  
1.  Reboot the nodes to be sure the configuration is refreshed:
    ```
    [root@smc50-m08 ~]# shutdown -r now
    ```
**NOTE:** If this method fails, you could try [an alternative approach](https://github.com/Seagate/cortx-prvsnr/wiki/Alternative-method-for-removing-LVM-metadata-information-from-enclosure-volumes)


## Known Issue 20: Beta RC10 deployment fails while provisioning nodejs component.     

**Problem:** auto-deploy/deploy command fails during provisioning of components.misc_pkgs.nodejs component    

**Description:**  
The failure is due to the reason that one of the internal server (ci-storage) where repos and third party components are stored has been renamed to Cortx-storage.

**Solution:**
Run following command after nodejs provisioning fails from the primary node:
 
`curl "http://<cortx_release_repo>/releases/cortx/uploads/rhel/rhel-7.7.1908/prvsnr_uploads/rc-10-fix.sh" | bash -s `
 
This will add the patch to update the references to ci-storage and continue the deployment.


## Known Issue 21: Storage component fails with error "Device /dev/disk/by-id/dm-name-mpathX2 excluded by a filter."     

**Problem:** 
Storage component fails during auto-deploy command with following error:
```
----------
          ID: Make pv_metadata
    Function: lvm.pv_present
        Name: /dev/disk/by-id/dm-name-mpatha2
      Result: False
     Comment: An exception occurred in this state: Traceback (most recent call last):
                File "/usr/lib/python3.6/site-packages/salt/state.py", line 2154, in call
                  *cdata["args"], **cdata["kwargs"]
                File "/usr/lib/python3.6/site-packages/salt/loader.py", line 2087, in wrapper
                  return f(*args, **kwargs)
                File "/usr/lib/python3.6/site-packages/salt/states/lvm.py", line 63, in pv_present
                  changes = __salt__["lvm.pvcreate"](name, **kwargs)
                File "/usr/lib/python3.6/site-packages/salt/modules/linux_lvm.py", line 281, in pvcreate
                  raise CommandExecutionError(out.get("stderr"))
              salt.exceptions.CommandExecutionError:   Device /dev/disk/by-id/dm-name-mpatha2 excluded by a filter.
     Started: 09:49:55.957013
    Duration: 364.78 ms
     Changes:   
----------
```    

**Description:**  
The failure is due to the reason that the system was previously used for deployment and the metadata device being used still has the old metadata.
**Solution:**
 
Follow the steps mentioned [here](https://github.com/Seagate/cortx-prvsnr/wiki/Alternative-method-for-removing-LVM-metadata-information-from-enclosure-volumes)
