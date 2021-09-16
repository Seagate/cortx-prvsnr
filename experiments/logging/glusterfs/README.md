# Glusterfs logging

## Prerequisite

- Kubernetes cluster is up and running
- Install glusterfs-server in all nodes. Follow installation [guide](https://www.gluster.org/install/)

## Create glusterfs cluster

- Follow glusterfs quickstart [guide](https://docs.gluster.org/en/latest/Quick-Start-Guide/Quickstart/) to setup cluster
- Create glusterfs endpoint and glusterfs service, refer [this](https://github.com/kubernetes/examples/tree/master/volumes/glusterfs) example

## Create PV

- kubectl apply -f [glusterfs-pv.yml](https://github.com/Seagate/cortx-prvsnr/blob/kubernetes/experiments/logging/glusterfs/glusterfs-pv.yml)
- `path`  should be name of the glusterfs volume

## Create PVC

- kubectl apply -f [glusterfs-pvc.yml](https://github.com/Seagate/cortx-prvsnr/blob/kubernetes/experiments/logging/glusterfs/glusterfs-pvc.yml)

## Create Pod

- Build docker image

  - docker build -t s3server .

- Create Pod which continuously logs into configured directory

  - kubectl apply -f [pod.yml](https://github.com/Seagate/cortx-prvsnr/blob/kubernetes/experiments/logging/glusterfs/pod.yml)

- This pod will add logs in `/share/var/log/cortx/s3server/s3server.log` file
