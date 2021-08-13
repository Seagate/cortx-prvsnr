# Setup Repo   

1.  Point to the supported YUM repos.  
    
    **Ref:** https://github.com/Seagate/cortx-prvsnr/tree/dev/files/etc/yum.repos.d
    
    **Note:** Any repos not mentioned at above location should be removed.

2.  Clean yum database  
    ```
    yum clean all  
    rm -rf /var/cache/yum  
    ```
    **Note:** You might be required to downgrade a few packages (like glibc and dependencies), in case there are setup issues.

3.  Install and setup Git on the target node [For Dev setup]  
    $ `yum install -y git`

4.  Update hostname (if necessary):  
    $ `hostnamectl set-hostname <hostname>`

5.  Install Provisioner CLI rpm (cortx-prvsnr-cli) from the release repo on all nodes to be provisioned (This rpm is required to setup passwordless `ssh` communication across nodes. Can be neglected for single node setup):  
    ```    
    yum install -y yum-utils  
    yum-config-manager --add-repo "http://<cortx_release_repo>/releases/cortx/github/master/rhel-7.7.1908/last_successful/"  
    yum install -y cortx-prvsnr-cli --nogpgcheck
    rm -rf /etc/yum.repos.d/cortx-storage*
    ```  

6.  Modify contents of file `~/.ssh/config` on primary node as suggested below:
    ```
    Host srvnode-1 <node-1 hostname> <node-1 fqdn>
        HostName <node-1 hostname or mgmt IP>
        User root
        UserKnownHostsFile /dev/null
        StrictHostKeyChecking no
        IdentityFile ~/.ssh/id_rsa_prvsnr
        IdentitiesOnly yes

    Host srvnode-2 <node-2 hostname> <node-2 fqdn>
        HostName <node-2 hostname or mgmt IP>
        User root
        UserKnownHostsFile /dev/null
        StrictHostKeyChecking no
        IdentityFile ~/.ssh/id_rsa_prvsnr
        IdentitiesOnly yes
    ```
    Copy `/root/.ssh/config` to other nodes

7.  Install Provisioner rpm (cortx-prvsnr) from the cortx release repo:  
    ```    
    yum install -y yum-utils  
    yum-config-manager --add-repo "http://<cortx_release_repo>/releases/cortx/github/master/rhel-7.7.1908/last_successful/"  
    yum install -y cortx-prvsnr --nogpgcheck
    rm -rf /etc/yum.repos.d/cortx-storage*
    ```  
    **Note:** replace rpm with appropriate rpm file in above command.

## Setup Salt

1.  Install SaltStack:  
    $ `yum install -y salt-master salt-minion`  

2.  Copy Salt config files:  
```
$ cp /opt/seagate/cortx/provisioner/srv/components/provisioner/salt_master/files/master /etc/salt/master
$ cp /opt/seagate/cortx/provisioner/srv/components/provisioner/salt_minion/files/minion /etc/salt/minion
```
3.  Setup minion_id  
    $ `vim /etc/salt/minion_id`  
    **Note**: Minion id for first node is `srvnode-1`. For subsequent nodes it would be `srvnode-n`, where n is the node count.  
    E.g. srvnode-2 for second node and so on.*  

4.  Set salt-master fqdn in `/etc/salt/minion`  
    ```
    # Set the location of the salt master server. If the master server cannot be
    # resolved, then the minion will fail to start.
    master: srvnode-1                   # <== Change this value to match salt-master fqdn
    ```

5.  Restart Salt Minion:  
    $ `systemctl restart salt-minion`  
    $ `systemctl restart salt-master`
    
6.  Register node into salt-master  
    $ `salt-key -L`  
    $ `salt-key -A -y`  

7.  Check if Salt is configured :  
    $ `salt '*' test.ping`  
