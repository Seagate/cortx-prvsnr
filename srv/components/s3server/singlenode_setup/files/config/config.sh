#!/bin/bash
# Exos-OS: Config

## Main config file
script_dir=$(dirname $0)
source $script_dir/config.common.sh

yesopt=""

print_usage_and_exit()
{
    echo "usage: $0 [-y] -c <eos-config-file.yaml>" \
        "[-e <data network inerface> [-E <mgmt network interface>]]"
    exit 1
}

while [[ $# -gt 0 ]]
do
    case $1 in
        -y)
            export yesopt="-y"
            shift
            ;;
        -c)
            [ -z $2 ] && echo -e "\nError: no eos config file provided" && \
                print_usage_and_exit
            export mini_conf=$2
            shift 2
            ;;
        -e)
            [ -z $2 ] && echo -e "\nError: no network interface provided" && \
                print_usage_and_exit
            ip -oneline -4 address show scope global up | grep -q $2
            if [ $? -ne 0 ]; then
                echo -e "\nError: The network interface provided doesn't" \
                    "exist or it doesn't have an ip address assigned to it."
                print_usage_and_exit
            fi
            export eth=$2
            shift 2
            ;;
        -E)
            [ -z $2 ] && echo -e "\nError: no management network interface" \
                "provided" && bootstrap_util_usage
            export mgmt_if=$2
            shift 2
            ;;
        *)
            echo "Unknown option- $1"
            print_usage_and_exit
            ;;
    esac
done

[ -z $mini_conf ] && echo -e "\nError: no eos config file provided" && \
    print_usage_and_exit
[ ! -e $mini_conf ] && echo -e "\nError config file $mini_conf doesn't exist" && \
    print_usage_and_exit

#TODO: Check the disk pattern provided in the mini config file are valid

$script_dir/pre_config.sh
$script_dir/config_sspl.sh
$script_dir/config_s3server.sh
$script_dir/config_mero-halon.sh
$script_dir/config_csm.sh
$script_dir/post_config.sh
