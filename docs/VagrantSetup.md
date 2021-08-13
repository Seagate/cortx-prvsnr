# Setup Vagrant
Follow https://www.vagrantup.com/intro/getting-started/index.html

# Initialize LDR-R1

## Initalize
1.  Create project folder:
```
mkdir ~/projects && cd ~/projects
```

1. Clone git repo for cortx-prvsnr:
```
git clone https://github.com/Seagate/cortx-prvsnr/
cd ~/projects/cortx-prvsnr
```

1. Add Vargrant box created for LDR-R1:
```
vagrant box add http://ci-storage.mero.colo.seagate.com/prvsnr/vendor/centos/vagrant.boxes/centos_7.5.1804.box --name centos_7.5.1804
```

## Start VagrantBox
The setup comes with Vagrantfile configured to create a 2 node Vagrant setup. However, due to [limitation with iterations in Vagrantfile](https://www.vagrantup.com/docs/vagrantfile/tips.html), each node needs to be initialized independently:
```
vagrant up srvnode-1 srvnode-2
```

To connect to node console over ssh:
```
vagrant ssh srvnode-1
vagrant ssh srvnode-2
```

For setting up S3Client VM node:
```
vagrant up s3client
```

To connect to node console over ssh:
```
vagrant ssh s3client
```

## Synchronize code
To synchronize code in git repo on host (`~/projects/cortx-prvsnr`) and `/opt/seagate/cortx/provisioner`:
```
vagrant rsync
```

## Destroy Vagrantbox
To cleanup Vagrant setup with deletion of all created boxes and supported virtual hardware:
```
vagrant destroy -f srvnode-1 srvnode-2
```
