#!/bin/bash

# This script configures s3 minio client
# Example:
# ./config_s3client.sh udxcloud http://s3.seagate.com BKIKJAA5BMMU2RHO6IBB V7f1CwQqAcwo80UEIJEjc5gVQUSSx5ohQ9GSrr12 /data/s3/ca.crt
set -e

script_dir=$(dirname $0)

[ "$#" -ne 4 ] &&
  echo "usage: $0 s3endpoint access-key secret-key ca-file" && exit 1

[ !  -f $4 ] && echo "Enter a valid CA file: $5" && exit 1

s3_end_point=$1

aws configure
aws configure set plugins.endpoint awscli_plugin_endpoint

aws configure set s3.endpoint_url $s3_end_point
aws configure set s3api.endpoint_url $s3_end_point

mkdir -p ~/.aws
cp $4 ~/.aws/ca.crt
grep -q ca_bundle ~/.aws/ca.crt ||
    sed -i '/^ *endpoint_url = http.*$/a ca_bundle = \/root\/.aws\/ca.crt' ~/.aws/config
