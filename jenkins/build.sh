#!/bin/bash -x

SCRIPT_DIR="$(dirname $0)"
#IMAGE=${1:-corxt-provisioner}

BUILD_URL=http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.9.2009/last_successful_prod

#docker build -t $IMAGE .
rpm -qa | grep -q docker-compose || yum install docker-compose
docker-compose -f $SCRIPT_DIR/docker-compose.yml build --force-rm \
  --build-arg BUILD_URL=$BUILD_URL cortx-provisioner
