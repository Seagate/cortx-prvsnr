#!/bin/bash

script_dir=$(dirname $0)
source $script_dir/eos-ops.sh

yesopt=""

usage()
{
    echo "usage: $0 [-y]"
    echo "Stop the eos cluster and clean up all config data"
    exit 1
}

while [[ $# -gt 0 ]]
do
    case $1 in
        -y)
            yesopt="-y"
            shift
            ;;
        *)
        echo "in *"
            echo "Unknown option- $1"
            usage
            exit 1
            ;;
    esac
done

cluster_stop_and_cleanup $yesopt
[ $? -ne 0 ] && echo "Could not stop the cluster" && exit 1
systemctl stop s3authserver
exit 0
