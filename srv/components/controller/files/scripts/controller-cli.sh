#!/bin/bash
set -euo pipefail

script_dir=$(dirname $0)
source $script_dir/parse_xml
source $script_dir/license.sh
source $script_dir/pools.sh
source $script_dir/volumes.sh

#TODO: Read system details from pillar file
#user="manage"
#pass="!manage"
#ssh_cred="/usr/bin/sshpass -p $pass"
#ssh_cmd="ssh $user@$host"
#remote_cmd="$ssh_cred $ssh_cmd"
xml_doc="/tmp/tmp.xml"
xml_cmd="/usr/bin/xmllint"
cli_cmd=
element=
ret_txt=

usage()
{
    echo "usage:"
    echo "$0 [-ac]"
    echo "$0 [-p -t <pool_type> -l <level> -m <pool name> -r <range of disks> " 
    echo "$0 [-l -n <no-of-vols> -s <size> -m <pool name>]" 
    echo "Options:"
    echo "-a :- Provision the controller with standard configuration (2 pools with 8 volumes)"
    echo "-c :- Cleanup all the volumes and pools available"
    echo "-p :- Create pool with following mandetory sub-options:"
    echo "      -t pool_type      :- type of pool- linear/virtual"
    echo "      -l level          :- pool configuration leve- adapt, r6, r5 etc"
    echo "      -m pool name      :- name of the pool to be created"
    echo "      -r range of disks :- range of disks e.g. '0.0-41', '0.42-83', '0.0-5,0.7-20,0.24'"
    echo "-l :- Create volume(s) with following mandetory sub-options:"
    echo "      -n no-of-vols     :- number of volumes to be created, e.g. 8"
    echo "      -s size           :- size of each volume, e.g. 1TB, 1000GB etc"
    echo "      -m pool name      :- name of the pool the volumes will be created on, either a or b" 
    echo " Sample commands:"
    echo " 1. To cleanup the existing pools and provision with the basic configuration (2 pools with 8 volumes each)"
    echo " $0 -ac"
    echo " 2. To create the pool with disk group named dg01 with disks ranging from 0 to 41 type virtual and level adapt"
    echo " $0 -p dg01 0.0-41 a"
    echo " 3. To create 8 luns/volumes of size 5TB each from pool a and map to all ports"
    echo " $0 -l 8 5TB a"
}

parse_args()
{
    [[ $# -lt 1 ]] && usage

    #TODO: Read specs from config file.
    cli_cmd=$1
    element=$2
    while [[ $# -gt 0 ]]
    do
        case $1 in

            -a)
                provision_all=true
                shift
                ;;
            -c)
                cleanup=true
                shift
                ;;
            -p)
                create_pool=true
                [ -z $2 ] && usage && exit 1
                pname=$2
                [ -z $3 ] && usage && exit 1
                drange=$3
                [ -z $4 ] && usage && exit 1
                ctrlid=$4
                shift 3
                ;;
            -l)
                create_lun=true
                [ -z $2 ] && usage&& exit 1
                nvols=$2
                [ -z $3 ] && usage && exit 1
                vsize=$3
                [ -z $4 ] && usage && exit 1
                dg=$4
                [ -z $5 ] && usage && exit 1
                initiators=$5
                [ -z $6 ] && usage && exit 1
                ctrlid=$6
                shift 6
                ;;
            -h)
                usage && exit 0
                ;;
            *)
                echo "Unknown option- $1"
                usage && exit 1
                ;;
        esac
    done
}

# run_cli_cmd()
# Arg1: cli command to run on enclosure, e.g. 'show version'
# Arg2: The element to be searched from the xml output of arg1 command.
# e.g. run_cli_cmd 'show version' 
cmd_run()
{
   _cmd=$1
   $remote_cmd $_cmd | tail -n +2 | head -n -1 > $xml_doc
   validate_xml $xml_doc
   # Check if command was successful or not
   cli_status_get $xml_doc
}

active_ports_get()
{
    _tmpfile=/tmp/ports
    # objects name in the xml
    object_basetype="port"
    # list of properties of the object basetype to get their values from the xml e.g. port with status
    property_list=("port" "status")
    echo "property_list=${property_list[@]}"

    # run command to get the available ports
    cmd_run 'show ports'
    # parse xml to get required values of properties
    parse_xml $xml_doc $object_basetype "${property_list[@]}" > $_tmpfile

    # Get the ports with the status 'Up'
    # Convert the ports (with status UP) listed on individual lines in to comma separated values
    # sed is to get rid of trailing comma
    port_list=`grep Up $_tmpfile | awk -vORS=, '{ print $1 }' | sed 's/,$/\n/'`

    echo $port_list
}

is_system_clean()
{
    _do_cleanup="false"
    provisioning_info_get $_do_cleanup 
}

disks_range_get()
{
    cmd_run 'show disks'

}

cleanup_provisioning()
{
    _cleanup=$1
    provisioning_info_get $_cleanup > $_tmp_file
    # TODO: find the logic to extract dg and pool
    # remove_dg
    # remove_pool
}

# Provision the cluster
# input parameters
# _pool_type : Type of the pool to be created e.g. virtual or linear
# _level : pool level - adapt, r6 etc.
# _npools : no of pools to be created (for virtual it's max 2)
# _nvols : no of volumes to be created per pool, default 8
# _vsize : size of the each volumes, by default 8 equal sized volume will
#          be created on a pool
# _pool1 : first pool 
# _pool1_dg : disk group name of the first pool
# _pool2 : second pool
# _pool2_dg : disk group name of the second pool
# 
provision()
{
    _pool_type=$1
    _level=$2
    _npools=$3
    _nvols=$4
    _vsize=$5
    _pool1="a"
    _pool1_dg="dg01"
    _pool2="b"
    _pool2_dg="dg02"
    is_system_clean
    drange=`disks_range_get`
    #divide disks in to two equal ranges - range1 & range2
    #get size of each pool
    #derive size of volumes to be created (equal sized volumes) poolsize/8
    _ports=`active_ports_get`
    disk_group_add $_pool_type $drange1 $_level $_pool1 $_pool1_dg
    disk_group_add $_pool_type $drange2 $_level $_pool2 $_pool2_dg
    _baselun=0 #starting lun number
    _basename="$_pool1_dg-" #starting name of volumes to be created
    volumes_create $_baselun $_basename- $_nvols $_pool1 $_vsize $_ports
    _baselun=$_nvols #starting lun number
    _basename="$_pool2_dg-" #starting name of volumes to be created
    volumes_create $_baselun $_basename $_nvols $_pool2 $_vsize $_ports
}

main()
{
    parse_args $@
    license_check
    if [ $default_provisioning = "true" ]; then
        if [ $cleanup = "true" ]; then
            cleanup_provisioning $cleanup
        fi
       provision virtual adapt 2 8 10GB
    fi
    echo "Done"
}

main