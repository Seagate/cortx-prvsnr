#!/bin/bash

node_spec="${1:-}"
ssh_cmd="ssh -o "ConnectTimeout=5""
ip=$($ssh_cmd $node_spec ip addr show $2 | grep "\<inet\>" |\
     awk '{ print $2 }' |  awk -F "/" '{ print $1 }')
echo ip=$ip