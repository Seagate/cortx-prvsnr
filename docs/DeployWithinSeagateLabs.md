# Deployment Within Seagate Labs 

**Problem**

It is essential to identify the affinities of the LUNs and associate right LUNs to the servers to ensure optimal performance over SAS cables. Due to cross-connect SAS cabling, it is difficult to find the LUNs with the right affinity. 

**Solution** 

Switch off the HBAs before deployment is executed before Provisioner states are triggered. Then re-enable them on successful deployment. 

 
**Utility for disabling/enabling HBA:** LSI util: http://cortx-storage.colo.seagate.com/seagate-internal/lsiutil/lsiutil.tar 

 
## Procedure 

1. Run cortx-prereqs script on both nodes.
2. Cleanup the storage for LVM drives and partitions https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-Stack#manual-fix-in-case-the-node-has-been-reimaged  
3. Download lsiutil package from link mentioned below both the nodes. 

```
  mkdir -p /opt/seagate 
  pushd /opt/seagate 
  curl -O http://cortx-storage.colo.seagate.com/seagate-internal/lsiutil/lsiutil.tar 
  popd 
```

4. Untar the package both the nodes. 

```
  pushd /opt/seagate 
  tar -xvf lsiutil.tar 
  popd 
```

5. Set execute permission both the nodes. 

```
  pushd /opt/seagate/lsiutil 
  chmod a+x * 
  popd 
```

6. Execute the lsiutil script to disable HBAs on primary node.

```
  pushd /opt/seagate/lsiutil 
  sh ./lsiutil.sh disable 
  popd 
```

7. Verify that cross-connectivity is disabled.

```
  [root@ <hostname> cortx-prvsnr]# ping -c1 10.0.0.2 

  PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data. 

  64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=9.30 ms 

  --- 10.0.0.2 ping statistics --- 

  1 packets transmitted, 1 received, 0% packet loss, time 0ms 

  rtt min/avg/max/mdev = 9.304/9.304/9.304/0.000 ms 
 
  ================================================= 
  [root@<hostname> cortx-prvsnr]# ping -c1 10.0.0.3 

  PING 10.0.0.3 (10.0.0.3) 56(84) bytes of data. 

  From 10.0.0.5 icmp_seq=1 Destination Host Unreachable 

  --- 10.0.0.3 ping statistics --- 

  1 packets transmitted, 0 received, +1 errors, 100% packet loss, time 0ms
```

8. Run deployment using autodeploy/new 2 stage deploy mechanism via: https://github.com/Seagate/cortx-prvsnr/wiki/Deployment-on-HW_Auto-Deploy OR https://github.com/Seagate/cortx-prvsnr/wiki/Setup-Cluster-Guide  

9. Enable the disabled HBA ports, if the deployment is successful in above step.
   
   `cd /opt/seagate/lsiutil/; sh ./lsiutil.sh enable`

10. Verify the cross-connectivity is re-enabled.

```
  [root@sm18-r20 cortx-prvsnr]# multipath -ll|grep -E "prio=50|prio=10"|wc –l 
  32 
```

11. Verify both the controller ips after deployment. 

```
  [root@ <hostname> cortx-prvsnr]# ping -c1 10.0.0.2 

  PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data. 

  64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=9.30 ms 

  --- 10.0.0.2 ping statistics --- 

  1 packets transmitted, 1 received, 0% packet loss, time 0ms 

  rtt min/avg/max/mdev = 9.304/9.304/9.304/0.000 ms 

  [root@ <hostname> cortx-prvsnr]# ping -c1 10.0.0.3 

  PING 10.0.0.2 (10.0.0.3) 56(84) bytes of data. 

  64 bytes from 10.0.0.3: icmp_seq=1 ttl=64 time=9.30 ms 

  --- 10.0.0.3 ping statistics --- 

  1 packets transmitted, 1 received, 0% packet loss, time 0ms 

  rtt min/avg/max/mdev = 9.304/9.304/9.304/0.000 ms 
