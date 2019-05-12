#!/bin/bash

set -e

script_dir=$(dirname $0)

url="http://jenkins.mero.colo.seagate.com/share/bigstorage/releases/hermi"

function install_s3server() {
    yum-config-manager --add "$url/s3server_uploads"
    local repo="jenkins.mero.colo.seagate.com_share_bigstorage_releases_hermi_s3server_uploads.repo"
    echo "gpgcheck=0" >> "/etc/yum.repos.d/$repo"

    yum install -y python34-jmespath
    yum install -y python34-botocore
    yum install -y python34-s3transfer

    yum install -y python34-boto3
    yum install -y python34-xmltodict

    yum-config-manager --add "$url/last_successful/s3server/repo"
    local repo="jenkins.mero.colo.seagate.com_share_bigstorage_releases_hermi_last_successful_s3server_repo.repo"
    echo "gpgcheck=0" >> "/etc/yum.repos.d/$repo"

    yum install -y s3server
    yum install -y s3server-debuginfo
    yum install -y s3iamcli
    yum install -y s3iamcli-devel

    sed -i 's/S3_ENABLE_STATS:  *false/S3_ENABLE_STATS: true/g' /opt/seagate/s3/conf/s3config.yaml
}

$script_dir/s3server/init.sh
install_s3server

