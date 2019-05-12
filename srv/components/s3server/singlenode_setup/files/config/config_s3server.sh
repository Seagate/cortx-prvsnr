#!/bin/bash

script_dir=$(dirname $0)

set -e

# Update haproxy config

mkdir -p /etc/haproxy/errors
cp $script_dir/503.http /etc/haproxy/errors/
cp $script_dir/haproxy.cfg /etc/haproxy/

hosts_file="/etc/hosts"
update_hosts()
{
    ip=$1
    entry=$2
    line=`grep $1 $hosts_file`
    #get line no of ip
    line_no=`grep -n $1 $hosts_file | cut -d: -f1`
    sed -i -e "$line_no"'d' $hosts_file
    sed -i "$line_no"'i'"$line $entry" $hosts_file
}
# Update haproxy config

line_cnt=`grep 127.0.0.1 $hosts_file | wc -l`
if [ $line_cnt -gt 1 ]; then
    echo "There are multiple entries for loopback ip 127.0.0.1 in $hosts_file"
    echo "Fix the $hosts_file and re run the command"
    exit 1
fi
#grep -q s3.seagate.com $hosts_file || update_hosts "127.0.0.1" "s3.seagate.com"
#grep -q iam.seagate.com $hosts_file || update_hosts "127.0.0.1" "iam.seagate.com sts.seagate.com"

systemctl restart haproxy
systemctl enable haproxy
systemctl enable slapd
systemctl enable s3authserver
