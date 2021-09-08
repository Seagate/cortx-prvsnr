#!/bin/bash -x

SCRIPT_DIR="$(dirname $0)"
IMAGE=${1:-provisioner}

BUILD_URL=http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.9.2009/last_successful_prod

# Validate
for rpm in $RPMS; do
  [ -f $rpm ] || { echo "error: nonexistent file $rpm"; exit 1; }
done

#docker build -t $IMAGE .
docker-compose -f $SCRIPT_DIR/docker-compose.yml build --force-rm --build-arg BUILD_URL="$BUILD_URL" --build-arg SRC="./src/" cortx-provisioner
