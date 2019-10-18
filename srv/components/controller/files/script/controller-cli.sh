#!/bin/bash

script_dir=$(dirname $0)

user="manage"
pass="!manage"
ssh_cred="/usr/bin/sshpass -p $pass"
ssh_cmd="ssh $user@$host"
remote_cmd="$ssh_cred $ssh_cmd"
xml_doc="/tmp/tmp.xml"
xml_cmd="/usr/bin/xmllint"
cli_cmd=
element=
ret_txt=

usage()
{
    echo "$0 <'controller_cmd'> ['element']"
    echo "e.g. $0 'show version' 'bundle-version'"
}

parse_args()
{
    #TODO: Read specs from config file.
    cli_cmd=$1
    element=$2

    [[ $# -lt 1 ]] && usage
}

cli_status_get()
{
    _xml_doc=$1
    status=`$xml_cmd -xpath '/RESPONSE/OBJECT/PROPERTY[@name="response-type"]/text()' $_xml_doc`
    [[ $status != "Success" ]] && echo "Command failed on the controller" && exit 1
    echo "Command run successfully"
}

parse_version()
{
    _xml_doc=$1
    _elements=$2
    _xpath_exp="'/RESPONSE/OBJECT[@basetype=\"$_basetype\"]/PROPERTY[@name=\"$_element\"]/text()'"
    # Parse command output
    ret_txt=`$xml_cmd -xpath $_xpath_exp $_xml_doc`

}

parse_xml()
{
    #TODO: accept object attribut and property attribute at cmd line
    _xml_doc=$1
    _element=$2
    _xpath_exp="'/RESPONSE/OBJECT/PROPERTY[@name=\"$_element\"]/text()'"
    # Parse command output
    ret_txt=`$xml_cmd -xpath $_xpath_exp $_xml_doc`
}

validate_xml()
{
    xml_doc=$1
    [[ `$xml_cmd $xml_doc` ]] && echo "Invalid XML input" && exit 1 
}

# run_cli_cmd()
# Arg1: cli command to run on enclosure, e.g. 'show version'
# Arg2: The element to be searched from the xml output of arg1 command.
# e.g. run_cli_cmd 'show version' 
cmd_run()
{
   _cmd=$1
   _element=$2
   $remote_cmd $_cmd | tail -n +2 | head -n -1 > $xml_doc
   validate_xml $xml_doc
   #Check if command was successful or not
   cli_status_get $_xml_doc
   [[ ! -z $_element ]] && parse_xml $xml_doc $_element
}

check_license()
{
    #TODO: Check if the virtualizztion license is enabled
    cmd_run 'show license'
}

cleanup_provisioning()
{
    cmd_run 'show volumes'
    cmd_run 'delete volumes volume-0'
    cmd_run 'show disk-groups'
    cmd_run 'delete pools 1 prompt yes' 
}

add_disk_group()
{
    _dg=$1
    _disks_range=$2
    _pool=$3
    _cmd="add disk-group type virtual disks $disks_range level adapt pool $_pool $_dg"
    echo "Creating disk group $_dg with $_disks_range disks"
    cmd_run $_cmd
}

check_active_ports()
{
    #TODO: extract port details
    cmd_run 'show ports'
}

create_volumes()
{
    _count=$1
    _size=$2
    _baselun=$3
    _basename=$4
    _ports=$5
    _pool=$6
    _cmd="create volume-set access rw baselun $_baselun basename $_basename count $_count pool $_pool size $_size ports $_ports"
    echo "Creating volume set with $_count volumes of size $_size in pool $_pool and mapped to ports $_ports"
    cmd_run $_cmd
}

main()
{

    #check_license
    #cleanup_provisioning

    add_disk_group 'dg01' '0.0-41' 'a'
    add_disk_group 'dg02' '0.42-83' 'b'
    check_active_ports
    create_volumes 8 '30TB' 0 'dg01-' 'A0-A3,B0-B3' 'a'
    create_volumes 8 '30TB' 8 'gd02-' 'A0-A3,B0-B3' 'b'
    echo "Done"
}

main
