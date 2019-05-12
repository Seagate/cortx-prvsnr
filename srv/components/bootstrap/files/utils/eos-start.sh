#!/bin/bash

script_dir=$(dirname $0)
source $script_dir/eos-ops.sh

yesopt=""

usage()
{
    echo "usage: $0 [-y]"
    echo "Start the eos cluster, if the cluster was previously configured."
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

## Check haproxy service
echo "Checking Status of haproxy service"
haprxy_status="$(systemctl status haproxy| grep Active | awk '{ print $2}')"
if [ $haprxy_status != "active" ]; then
    echo "haproxy service is not active, starting"
    systemctl start haproxy
    haprxy_status="$(systemctl status haproxy| grep Active | awk '{ print $2}')"
    [ $haprxy_status != "active" ] && echo "Could not start haproxy" && exit 1
fi

## Check slapd service
echo "Checking status of slapd service"
slapd_status="$(systemctl status slapd | grep Active | awk '{ print $2}')"
if [ $slapd_status != "active" ]; then
    echo "slapd service is not active, starting"
    systemctl start slapd
    slapd_status="$(systemctl status slapd | grep Active | awk '{ print $2}')"
    [ $slapd_status != "active" ] && echo "Could not start slapd" && exit 1
fi

## Check s3authserver service
echo "Checking status of s3Authserver service"
s3_status="$(systemctl status s3authserver | grep Active | awk '{ print $2}')"
if [ $s3_status != "active" ]; then
    echo "s3Authserver service is not active, starting"
    systemctl start s3authserver
    s3_status="$(systemctl status s3authserver | grep Active | awk '{ print $2}')"
    [ $s3_status != "active" ] && echo "Could not start s3Authserver" && exit 1
fi

cluster_eos_start $yesopt
[ $? -ne 0 ] && echo "Could not start the cluster" && exit 1
exit 0
