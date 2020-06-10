<h2>Wrapper for Single Node, Dual Node EOS Intslalltion through Provisioner<h2>


<h3><i>How to use it ?? </i></h3>
  

<b>Single Node : </b>
```
curl -s http://gitlab.mero.colo.seagate.com/re-poc/node-setup/raw/master/single-node/install.sh | bash /dev/stdin -b '${build}'
```



<b>Dual Node : </b>
```
curl -s http://gitlab.mero.colo.seagate.com/re-poc/node-setup/raw/master/dual-node/install.sh | bash /dev/stdin -b '${build}' -s '${node1Host}' -c '${node2Host}

```

<i>Note: For dual node passwordless ssh should be done before using this script</i>


<i>Parameters:</i>

| paramerter Name | value | Type | Single Node | Dual Node |
| ------ | ------ | ------ | ------ | ------ |
| -b | Build Number | Required | Yes | Yes | 
| -s | Server Node Host Name   | Required | No | Yes |
| -c | Client Host Name   |Required | No | Yes |

    




<h3><i>How it's done ?? </i></h3>

  - This script follows the node setup steps in ees-prvsnr [QuickStart-Guide](http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr/wikis/Setup-Guides/QuickStart-Guide).
  - This script sets some default values for the required params  
      - mgmt0 => **eth0**    
      - data0 => **eth1**  
      - HostName => **Server Host Name** (for single node)   
     