#!/bin/bash

# assumptions:
# - provisioner api is installed
# - current directory is a provisioner cli directory (TODO improve)

set -eux

mgmt_if="${1:-enp0s8}"
data_if="${2:-enp0s8}"
mgmt_device="${3:-/dev/sdb}"
data_device="${4:-/dev/sdc}"
eos_release="${5:-integration/centos-7.7.1908/last_successful}"

# configure cluster.sls
pillar_file_tmp="$(realpath ./pillar.sls.tmp)"
default_gateway="$(ip route | grep default | head -1 | awk '{print $3}')"

bash ./configure-eos -p cluster >"$pillar_file_tmp"
cat "$pillar_file_tmp"
sed -i "s~mgmt_if: .*~mgmt_if: $mgmt_if~g" "$pillar_file_tmp"
sed -i "s~data_if: .*~data_if: $data_if~g" "$pillar_file_tmp"
sed -i "s~/dev/sdb.*~$mgmt_device~g" "$pillar_file_tmp"
sed -i "s~/dev/sdc.*~$data_device~g" "$pillar_file_tmp"
sed -i "s~gateway: .*~gateway: $default_gateway~g" "$pillar_file_tmp"
cat "$pillar_file_tmp"
bash ./configure-eos -vv -f "$pillar_file_tmp" cluster

bash ./configure-eos -p release >"$pillar_file_tmp"
cat "$pillar_file_tmp"
sed -i "s~target_build: .*~target_build: $eos_release~g" "$pillar_file_tmp"
cat "$pillar_file_tmp"
bash ./configure-eos -vv -f "$pillar_file_tmp" release

rm -f "$pillar_file_tmp"
