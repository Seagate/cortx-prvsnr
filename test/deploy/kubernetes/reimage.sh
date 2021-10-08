#!/bin/bash
# Defaults
IMAGE_NAME="ghcr.io/seagate/cortx-all"
IMAGE_TAG="2.0.0-latest-custom-ci"
IMAGE_LIST="/tmp/cortx_images.log"
LOCAL_PATH="/etc/cortx"
SHARE_PATH="/share"

echo -e "NOTE: This script will cleanup resources for fresh deployment";
echo -e "      Please run this script on all cluster nodes";

# Increase Resources
echo -e "Increasing virtual memory limit";
sysctl -w vm.max_map_count=30000000;

# Delete previous images
docker images | grep "cortx-all" | tr -s ' ' | cut -d ' ' -f 3 > $IMAGE_LIST;
for IMAGE_MATCH in $(cat $IMAGE_LIST); do
    echo -e "Deleting Image ID: $IMAGE_MATCH";
    docker rmi -f $IMAGE_MATCH;
done

# Download latest image
echo -e "Pulling Latest Image: $IMAGE_NAME:$IMAGE_TAG";
docker pull $IMAGE_NAME:$IMAGE_TAG;

# Delete local
echo -e "Cleaning Local: $LOCAL_PATH";
rm -rf $LOCAL_PATH/*;

# Delete share
echo -e "Cleaning Share: $SHARE_PATH";
rm -rf $SHARE_PATH/*;

exit 0;
