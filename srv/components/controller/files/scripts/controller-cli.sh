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

check_active_ports()
{
    #TODO: extract port details
    cmd_run 'show ports'
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
