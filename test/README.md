## Preparation
***

Follow below steps for preparing test enviorment for running provisioner tests
```bash
# Install rpm-build rpm
$ yum install rpm-build -y

# Build utils RPM
$ git clone https://github.com/Seagate/cortx-utils -b main
$ sudo pip3 install -r https://raw.githubusercontent.com/Seagate/cortx-utils/main/py-utils/python_requirements.txt
$ sudo pip3 install -r https://raw.githubusercontent.com/Seagate/cortx-utils/main/py-utils/python_requirements.ext.txt
$ sudo yum install -y gcc rpm-build python36 python36-pip python36-devel python36-setuptools openssl-devel libffi-devel python36-dbus
$ cd cortx-utils/
$ ./jenkins/build.sh -v 2.0.0 -b 2
$ cd ./py-utils/dist
$ sudo yum install -y cortx-py-utils-*.noarch.rpm

# Build provisioner RPM
$ git clone https://github.com/Seagate/cortx-prvsnr -b main
$ cd cortx-prvsnr
$ rm -rf ./dist
$ ./jenkins/build.sh
$ ls ./dist/
$ sudo yum localinstall -y ./dist/cortx-provisioner-2.0.0-1_abcd056.noarch.rpm
$ cortx_setup --help

# Create env variable NODE_NAME on node with hostname as value
$ export NODE_NAME=<node-hostname>

# Prepare cluster.yaml and config.yaml files
$ cp /opt/seagate/cortx/provisioner/conf/config.yaml.sample /etc/cortx/solution/config.yaml
$ cp /opt/seagate/cortx/provisioner/conf/cluster.yaml.sample /etc/cortx/solution/cluster.yaml
# Note: Edit cluster.yaml file by putting vm machine-id and hostname in control-node section

# Mock control node
$ mkdir /opt/seagate/cortx/csm
$ mkdir /opt/seagate/cortx/csm/bin
$ cat <<EOF >> /opt/seagate/cortx/csm/bin/csm_setup
#!/bin/bash

EOF
$ chmod +x /opt/seagate/cortx/csm/bin/csm_setup

# Prapare RELEASE.INFO file on vm at location : /opt/seagate/cortx/RELEASE.INFO

# Prepare machine-id symlink
$ rm -rf /etc/machine-id
$ ln -s /etc/cortx/config/machine-id /etc/machine-id

# Note : everytime /etc/machine-id will be changed by provisioner so it needs to be updated in cluster.yaml everytime before rerunning provisioner.
```

## Testing Manually

Run apply command
```python
config apply -f yaml://`pwd`/config.yaml -c yaml:///tmp/cluster.conf
config apply -f yaml://`pwd`/cluster.yaml -c yaml:///tmp/cluster.conf
```

Run bootstrap command
```python
cluster bootstrap -c yaml:///tmp/cluster.conf
```


Run the following command  
**Running The Tests**
```python
./test_provisioner.py
```
