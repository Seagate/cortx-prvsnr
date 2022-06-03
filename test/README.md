## Preparation
***

Prepare input for cortx_setup. There are two files in this folder.  
a. cluster.yaml  
b. config.yaml  

Install cortx-utils and cortx-provisioner, cortx-components rpms.Make sure PYTHON_PATH includes src folder, if you are not using rpm.  
```bash
yum install -y yum-utils
sudo pip3 install -r https://raw.githubusercontent.com/Seagate/cortx-utils/main/py-utils/python_requirements.txt
sudo pip3 install -r https://raw.githubusercontent.com/Seagate/cortx-utils/main/py-utils/python_requirements.ext.txt
# Install cortx py-utilsby follwing below document
https://github.com/Seagate/cortx-utils/wiki/Build-and-Install-cortx-py-utils

# Build Cortx-provisioner rpm
yum install rpm-build -y
rm -rf ./dist
./jenkins/build.sh # Build RPM
ls ./dist/
sudo yum localinstall ./dist/cortx-provisioner-2.0.0-1_c9e8891.noarch.rpm
cortx_setup --help

# Mock the components to run the bootstrap command
echo -e "#!/bin/bash\necho $*" > /opt/seagate/cortx/utils/bin/utils_setup;
echo -e "#!/bin/bash\necho $*" > /opt/seagate/cortx/csm/bin/csm_setup;
chmod +x /opt/seagate/cortx/hare/bin/utils_setup;
chmod +x /opt/seagate/cortx/motr/bin/csm_setup;
```

## Testing Manually

Run apply command
```python
cortx_setup.py config apply -f yaml://`pwd`/config.yaml -c yaml:///tmp/cluster.conf
cortx_setup.py config apply -f yaml://`pwd`/cluster.yaml -c yaml:///tmp/cluster.conf
```

Run bootstrap command
```python
cortx_setup.py cluster bootstrap -c yaml:///tmp/cluster.conf
```

output will look something like this...
```bash
motr_setup post_install --config yaml:/etc/cortx/cortx.conf --services io
hare_setup post_install --config yaml:/etc/cortx/cortx.conf --services all
s3_setup post_install --config yaml:/etc/cortx/cortx.conf --services io,auth,bg_consumer
utils_setup post_install --config yaml:/etc/cortx/cortx.conf --services message_bus
csm_setup post_install --config yaml:/etc/cortx/cortx.conf --services agent
motr_setup post_install --config yaml:/etc/cortx/cortx.conf --services fsm
s3_setup post_install --config yaml:/etc/cortx/cortx.conf --services bg_producer
```

Run the following command  
**Running The Tests**
```python
./test_provisioner.py
```
