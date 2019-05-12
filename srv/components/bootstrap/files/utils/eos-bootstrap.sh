#!/bin/bash

script_dir=$(dirname $0)
source $script_dir/eos-ops.sh

yn=""

while [[ $# -gt 0 ]]
do
    case $1 in
        -y)
            yn="-y"
            shift
            ;;
        -c)
            [ -z $2 ] && bootstrap_util_usage && exit 1
            mini_conf=$2
            [ ! -e $mini_conf ] && echo "file $mini_conf doesn't exist" && exit 1
            do_genfacts="true"
            shift 2
            ;;
        -e)
            [ -z $2 ] && echo -e "\nError: no network interface provided" && \
                bootstrap_util_usage
            if [ $single_node_cluster = "yes" ]; then
                ip -oneline -4 address show scope global up | grep -q $2
                if [ $? -ne 0 ]; then
                    echo -e "\nError: The network interface provided doesn't" \
                        "exist or it doesn't have an ip address assigned to it."
                    bootstrap_util_usage
                fi
            fi
            net_if=$2
            shift 2
            ;;
        -E)
            [ -z $2 ] && echo -e "\nError: no management network interface" \
                "provided" && bootstrap_util_usage
            mgmt_if=$2
            shift 2
            ;;
        *)
            echo "Unknown option- $1"
            bootstrap_util_usage
            exit 1
            ;;
    esac
done

cluster_stop_and_cleanup $yn
cluster_enable_stats $yn
cluster_bootstrap $yn
[ $? -ne 0 ] && echo "Error in bootstrap, exiting.." && exit 1
echo "complete"
exit 0
