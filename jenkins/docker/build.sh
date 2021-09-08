#!/bin/bash -x

SCRIPT_DIR="$(dirname $0)"
IMAGE=${1:-cortx-provisioner}

BUILD_URL=http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.9.2009/last_successful_prod

mkdir -p $SCRIPT_DIR/tmp
rm -rf $SCRIPT_DIR/tmp/*
cp -rpf $SCRIPT_DIR/../../src/* $SCRIPT_DIR/tmp/
docker build --build-arg BUILD_URL=$BUILD_URL -t $IMAGE $SCRIPT_DIR
