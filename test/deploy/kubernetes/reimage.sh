#!/bin/bash
# Defaults
IMAGE_NAME="ghcr.io/seagate/cortx-all"
LATEST_TAG="2.0.0-latest-custom-ci"
CUSTOM_TAG="2.0.0-latest-custom-ci"
IMAGE_LIST="/tmp/cortx_images.log"
LOCAL_PATH="/var/cortx"
SHARE_PATH="/share"
CONFIG_PATH="/etc/cortx"

function print_header {
    echo -e "--------------------------------------------------------------------------"
    echo -e "$1"
    echo -e "--------------------------------------------------------------------------"
}

function show_usage {
    print_header "usage: $(basename $0) [--tag CORTX-ALL IMAGE TAG]"
    print_header " CUSTOM IMAGE TAG    : Provide Custom cortx-all image tag (Default: Latest)"
    exit 1
}

while [ $# -gt 0 ];  do
    case $1 in
    --tag )
        shift 1
        CUSTOM_TAG=$1
        ;;
    * )
        echo -e "Invalid argument provided : $1"
        show_usage
        exit 1
        ;;
    esac
    shift 1
done

print_header "NOTE: This script will cleanup resources for fresh deployment";
print_header "      Please run this script on all cluster nodes";

# Install Helm
print_header "Installing helm";
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3;
chmod 700 get_helm.sh;
./get_helm.sh;

# Increase Resources
print_header "Increasing virtual memory limit";
sysctl -w vm.max_map_count=30000000;

# Delete previous images
docker images | grep "cortx-all" | tr -s ' ' | cut -d ' ' -f 3 > $IMAGE_LIST;
for IMAGE_MATCH in $(cat $IMAGE_LIST); do
    print_header "Deleting Image ID: $IMAGE_MATCH";
    docker rmi -f $IMAGE_MATCH;
done

# Download latest cortx image
print_header "Pulling Cortx-all Docker image with tag $CUSTOM_TAG";
docker pull $IMAGE_NAME:$CUSTOM_TAG;
print_header "Renaming Custom Image: $IMAGE_NAME:$CUSTOM_TAG to Latest Image: $IMAGE_NAME:$LATEST_TAG";

# Pull 3rd party Docker images
docker pull ghcr.io/seagate/symas-openldap:latest;
docker pull bitnami/kafka;
docker pull rancher/local-path-provisioner:v0.0.20;
docker pull bitnami/zookeeper;
docker pull hashicorp/consul:1.10.2;
docker pull busybox;

docker tag $IMAGE_NAME:$CUSTOM_TAG $IMAGE_NAME:$LATEST_TAG;

# Delete local
print_header "Cleaning Local: $LOCAL_PATH";
rm -rf $LOCAL_PATH/*;

# Delete config
print_header "Cleaning Config: $CONFIG_PATH";
rm -rf $CONFIG_PATH/*;

# Delete share
print_header "Cleaning Share: $SHARE_PATH";
rm -rf $SHARE_PATH/*;
exit 0;
