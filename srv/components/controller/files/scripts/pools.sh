disk_group_add()
{
    #Command to add disk grup
    #Add virtual disk group
    #add disk-group type virtual disks <0.0-19> level adapt pool <a> <dg01>
    #Add linear disk group
    #add disk-group type linear disks 1.1-12 level adapt ALDG
    _type=$1
    _drange=$2
    _level=$3
    _pool=$4
    _dg=$5
    if [ $type = "virtual" ]; then
        _pool_opt="pool $_pool"
    else
        _pool_opt=""
    fi
    _cmd_opts="type $_type disks $_drange level $_level $_pool_opt $_dg"
    _cmd="add disk-group $_cmd_opts"
    echo "Creating disk group $_dg of type $_type, level $_level and with"\
         " $_drange disks"
    cmd_run $_cmd
}

pools_info_get()
{
    _cleanup=$1
    _tmp_file="/tmp/pools"
    _object_basetype="pools"
    _property_list=("name" "health")

    # run command to get the pools
    cmd_run 'show pools'
    # parse xml to get required values of properties
    parse_xml $xml_doc $object_basetype "${property_list[@]}" > $_tmpfile

    parse_xml $xml_doc $_object_basetype "${_property_list[@]}" > $_tmp_file
    _lines=`cat $_tmp_file | wc -l`
    [[ $_lines -ne 0 && $_cleanup = "false" ]] && {
        echo "The controller is not in clean state, there are pool(s)"\
        " created. Please delete the pool(s) and rerun the command."
        echo "OR Run the command with -c options"
        exit 1
    }
    cat $_tmp_file
}

disk_groups_get()
{
    _cleanup=$1
    _tmp_file="/tmp/dgs"
    _object_basetype="disk-groups"
    _property_list=("name" "size" "freespace" "pool" "status" "health")

    # run command to get the pools
    cmd_run 'show disk-groups'
    # parse xml to get required values of properties
    parse_xml $xml_doc $object_basetype "${property_list[@]}" > $_tmpfile

    parse_xml $xml_doc $_object_basetype "${_property_list[@]}" > $_tmp_file
    _lines=`cat $_tmp_file | wc -l`
    [[ $_lines -ne 0 && $_cleanup = "false" ]] && {
        echo "The controller is not in clean state, there are disk-group(s)"\
        " created. Please delete the disk group(s) and rerun the command again."
        echo "OR Rerun the command with -c options"
        exit 1
    }
    cat $_tmp_file
}

provisioning_info_get()
{
    _cleanup=$1
    _tmp_file="/tmp/provisiong"
    echo "disk groups" > $_tmp_file
    disk_groups_get $_cleanup >> $_tmp_file
    echo "pools" > $_tmp_file
    pools_info_get $_cleanup >> $_tmp_file
    echo $_tmp_file
}

remove_dg()
{
    _dg=$1
    cmd_run 'remove disk-group $_dg' > $xml_doc
    cli_status_get $xml_doc
}

remove_pool()
{
    _pool=$1
    cmd_run 'delete pools $_pool' > $xml_doc
    cli_status_get $xml_doc
}