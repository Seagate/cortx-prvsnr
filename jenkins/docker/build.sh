#!/bin/bash -x

SCRIPT_DIR="$(dirname $0)"
IMAGE=${1:-cortx-provisioner}

BUILD_URL=http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.9.2009/last_successful_prod
RPM_DIST_DIR=$SCRIPT_DIR/../../dist

[ -d $RPM_DIST_DIR ] && rm -rf $RPM_DIST_DIR
$SCRIPT_DIR/../build.sh
PROV_RPM=$(ls $RPM_DIST_DIR | grep noarch)

mkdir -p "$SCRIPT_DIR"/tmp
rm -rf "$SCRIPT_DIR"/tmp/*

cp $RPM_DIST_DIR/$PROV_RPM $SCRIPT_DIR/tmp/

ls "$SCRIPT_DIR"/tmp/

docker build --build-arg RPM="$PROV_RPM" --build-arg BUILD_URL=$BUILD_URL -t $IMAGE $SCRIPT_DIR
