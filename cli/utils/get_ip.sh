#!/bin/bash

node_spec="${1:-}"
ssh_cmd="ssh -o "ConnectTimeout=5""
ip=$($ssh_cmd $node_spec ip addr show $2 | grep "\<inet\>" |\
     awk '{ print $2 }' |  awk -F "/" '{ print $1 }')
if [ ! -z $ip ]; then
     echo $ip
     exit 0
else
    echo "Error"
    exit 1
fi
