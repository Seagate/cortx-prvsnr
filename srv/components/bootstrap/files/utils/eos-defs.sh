#!/bin/bash

script_dir=$(dirname $0)

single_node_cluster="yes"

pdsh_cmd="pdsh -w"
if [ "$single_node_cluster" = "no" ]; then
    ssu_hosts="ssu[1-6]-h1"
    client_hosts="qb01n[1-4]-h1"
    all_hosts="$ssu_hosts,$client_hosts"
    RC_host="ssu1-h1"
    RC_halon_port="172.16.1.1:9070"
    pdsh_RC_host="$pdsh_cmd $RC_host"

    pdsh_ssu_hosts="$pdsh_cmd $ssu_hosts"
    pdsh_client_hosts="$pdsh_cmd $client_hosts"
    pdsh_all_nodes="$pdsh_cmd $all_hosts"
else
    RC_host=""
    pdsh_RC_node=""
    pdsh_ssu_hosts=""
    pdsh_client_hosts=""
    pdsh_all_nodes=""
    all_hosts=""
fi

do_genfacts="false"
n_data_units=8
n_parity_units=2
net_if=
mgmt_if=
net_if_ip=
mgmt_if_ip=
mini_conf="$script_dir/../mini-cluster-config.yaml"
halon_facts="/etc/halon/halon_facts.yaml"
halond_conf="/etc/sysconfig/halond"
lnet_conf="/etc/modprobe.d/lnet.conf"

use_stx_prvsnr="no"
