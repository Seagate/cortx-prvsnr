## Preparation
***

Prepare input for cortx_setup. There are two files in this folder.  
a. cluster.yaml  
b. config.yaml  

Install cortx-utils and cortx-provisioner, cortx-components rpms.Make sure PYTHON_PATH includes src folder, if you are not using rpm.  
```bash
export CORTX_RELEASE_REPO=<<build-link of kubernetes branch>>
yum install -y yum-utils
yum-config-manager --add-repo "${CORTX_RELEASE_REPO}/3rd_party/"
yum-config-manager --add-repo "${CORTX_RELEASE_REPO}/cortx_iso/"
cat <<EOF >/etc/pip.conf
[global]
timeout: 60
index-url: $CORTX_RELEASE_REPO/python_deps/
trusted-host: $(echo $CORTX_RELEASE_REPO | awk -F '/' '{print $3}')
EOF
yum install --nogpgcheck -y python3 cortx-prereq
yum install --nogpgcheck -y cortx-py-utils python36-cortx-prvsnr
yum install --nogpgcheck -y cortx-provisioner
yum install --nogpgcheck -y cortx-motr cortx-hare cortx-s3server cortx-csm_agent cortx-csm_web
```

## Testing Manually

Run apply command
```python
cortx_setup.py config apply -f yaml://`pwd`/config.yaml -c yaml:///tmp/mp.conf
cortx_setup.py config apply -f yaml://`pwd`/cluster.yaml -c yaml:///tmp/mp.conf
```

Run bootstrap command
```python
cortx_setup.py cluster bootstrap -f yaml:///tmp/mp.conf -c yaml:///tmp/mp.conf
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
