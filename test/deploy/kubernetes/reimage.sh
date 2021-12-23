#!/bin/bash
# Defaults
IMAGE_NAME="ghcr.io/seagate/cortx-all"
CUSTOM_TAG=
LOCAL_PATH="/var/cortx"
SHARE_PATH="/share"
CONFIG_PATH="/etc/cortx"

function print_header {
    echo -e "--------------------------------------------------------------------------"
    echo -e "$1"
    echo -e "--------------------------------------------------------------------------"
}

function show_usage {
    echo -e "Usage: $(basename $0) [--tag CUSTOM-TAG]"
    echo -e "Default Image: ghcr.io/seagate/cortx-all:2.0.0-latest-custom-ci"
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

echo -e "NOTE: This script will cleanup resources for fresh deployment";
echo -e "      Please run this script on all cluster nodes";

# Install Helm
print_header "Installing helm";
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3;
chmod 700 get_helm.sh;
./get_helm.sh;

# Increase Resources
print_header "Increasing virtual memory limit";
sysctl -w vm.max_map_count=30000000;

if [ -n "$CUSTOM_TAG" ]; then
    # Download latest new image
    echo -e "Pulling New Image: $IMAGE_NAME:$CUSTOM_TAG";
    docker pull $IMAGE_NAME:$CUSTOM_TAG;
fi

# Pull 3rd party Docker images
print_header "Updating 3rdParty Image: symas-openldap";
docker pull ghcr.io/seagate/symas-openldap:latest;

print_header "Updating 3rdParty Image: Kafka";
docker pull bitnami/kafka;

print_header "Updating 3rdParty Image: Rancher";
docker pull rancher/local-path-provisioner:v0.0.20;

print_header "Updating 3rdParty Image: Zookeeper";
docker pull bitnami/zookeeper;

print_header "Updating 3rdParty Image: Consul";
docker pull hashicorp/consul:1.10.4;

print_header "Updating 3rdParty Image: Busybox";
docker pull busybox;

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
