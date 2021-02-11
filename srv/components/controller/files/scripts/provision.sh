#!/bin/bash
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

script_dir=$(dirname $0)

ftp_log="$logdir/fw_upgrade.log"

if [ -f $ftp_log ]; then
    ts=$(date +"%Y-%m-%d_%H-%M-%S")
    yes | cp -f $ftp_log ${logdir}/fw_upgrade_${ts}.log
fi

sftp_log="$logdir/sftp_fw_upgrade.log"

if [ -f $sftp_log ]; then
    ts=$(date +"%Y-%m-%d_%H-%M-%S")
    yes | cp -f $sftp_log ${logdir}/sftp_fw_upgrade_${ts}.log
fi

ftp_op_timeout=false
ftp_kill_timeout=false
ftp_pid=
controller_A_ver=
controller_B_ver=
export ctrl_activity_a=
export ctrl_activity_b=
ret_fw_versions_compare=99 # 99 - default value
fw_update_status=99 
bundle_fw_ver=

# run_cli_cmd()
# Arg1: cli command to run on enclosure, e.g. 'show version'
# Arg2: The element to be searched from the xml output of arg1 command.
# e.g. run_cli_cmd 'show version' 
cmd_run()
{
   _cmd="$1"
   _tmp_xml="$tmpdir/tmp.xml"
    #echo "cmd_run(): running: '$remote_cmd $_cmd'" >> $logfile
   echo $_cmd | grep -q -E "restart|shutdown" && {
       timeout -k9 -s6 20s $remote_cmd $_cmd > $_tmp_xml
   } || {
       $remote_cmd $_cmd > $_tmp_xml 
   }
   ret=$?
   echo "cmd_run():cmd ret val: $ret" >> $logfile
   [ $ret -eq 0 ] || {
       # Don't exit on controller restart or shutdown
       # On successful restart or shutdown there will
       # be no response from the enclosure, handle it.
       echo $_cmd | grep -q -E "restart|shutdown" && return $ret
       echo "Error running ssh command: $remote_cmd $_cmd"
       echo "Recheck the host details and run the command again"
       exit 1
   }
   cat $_tmp_xml | tail -n +2 | head -n -1 > $xml_doc
   validate_xml
   # Check if command was successful or not
   cli_status_get
}

license_check()
{
    tmp_file="$tmpdir/license"
    [ -f $tmp_file ] && rm -rf $tmp_file
    # objects name in the xml
    object_basetype="license"
    # list of properties of the object basetype to get their values from the
    # xml e.g. license for virtualization & vds
    property_list=("virtualization" "vds")
    echo "license_check(): Checking licenses "${property_list[@]}"" >> $logfile

    # run command to get the available ports
    echo "Checking licenses.."
    _cmd="show license"
    echo "license_check(): Running command: '$_cmd'" >> $logfile
    cmd_run "$_cmd"
    # parse xml to get required values of properties
    parse_xml $xml_doc $object_basetype "${property_list[@]}" > $tmp_file

    echo "------licenses---------" >> $logfile
    cat $tmp_file >> $logfile
    echo "-----------------------" >> $logfile
    # Get the status of virtualization license
    virtualization_license=`cat $tmp_file | awk '{ print $1 }'`
    [ "$virtualization_license" = "Disabled" -a "$pool_type" = "virtual" ] && {
        echo "Error: Can not create virtual pool, the virtualization"\
            "license is not installed."
        echo "Please install the virtualization license and try again"
        rm -rf $tmp_file
        exit 1
    }
    # Get the status of vds license
    # Not needed as of now
    # vds_license=`cat $tmp_file | awk '{ print $2 }'`
    #[[ "$vds_license" = "Enabled" ]] || {
    #    echo "license_check(): VDS license is not installed." >> $logfile
    #}
    echo "Virtualization license is enabled" >> $logfile
}

active_ports_get()
{
    _tmpfile=$tmpdir/ports
    # objects name in the xml
    object_basetype="port"
    # list of properties of the object basetype to get
    # their values from the xml e.g. port with status
    property_list=("port" "status")
    echo "active_ports_get(): Entry" >> $logfile
    echo "active_ports_get(): property_list=${property_list[@]}" >> $logfile

    _cmd="show ports"
    echo "active_ports_get(): running command: '$_cmd'" >> $logfile
    # run command to get the available ports
    cmd_run "$_cmd"
    # parse xml to get required values of properties
    parse_xml $xml_doc $object_basetype "${property_list[@]}" > $_tmpfile

    # Get the ports with the status 'Up'
    # Convert the ports (with status UP) listed on individual
    # lines in to comma separated values
    # sed is to get rid of trailing comma
    port_list=`grep Up $_tmpfile | awk -vORS=, '{ print $1 }' | sed 's/,$/\n/'`
    echo "---port list---" >> $logfile
    echo $port_list >> $logfile
    echo "---------------" >> $logfile
    rm -rf $_tmpfile
    echo $port_list
}

cleanup_provisioning()
{
    _pools="$tmpdir/cleanup_pools"
    _prv_info="$tmpdir/prov_info"
    _xml_obj_base="pools"
    _xml_obj_plist=("name" "health")

    echo "cleanup_provisioning(): entry" >> $logfile
    pools_info_get $_xml_obj_base "${_xml_obj_plist[@]}" > $_pools
    [ ! -s $_pools ] && {
        echo "No pools in the system, nothing to cleanup."
        rm -rf $_pools
        return 0
    }
    echo "cleanup_provisioning(): deleting pools:" >> $logfile
    echo "cleanup_provisioning(): -----pools----------" >> $logfile
    cat $_pools >> $logfile
    echo "cleanup_provisioning():--------------------" >> $logfile
    for pool in `cat $_pools | tail -n+3 | awk '{ print $1 }'`
    do
        echo "Deleting pool $pool"
        _cmd="delete pools prompt yes $pool"
        echo "cleanup_provisioning(): running command:"\
            "'$_cmd'" >> $logfile
        cmd_run "$_cmd"
        echo "Pool $pool deleted successfully"
    done

    echo "Checking the provisioning again.."
    provisioning_info_get > $_prv_info
    [ -s $_prv_info ] || {
        echo "Cleanup done successfully"
        rm -rf $_pools $_prv_info
        return 0
    }
    echo "Error: Cleanup is incomplete, checking what did not get cleaned up"
    echo "getting pool details..."
    pools_info_get $_xml_obj_base "${_xml_obj_plist[@]}" > $_pools
    [ -s $_pools ] && {
        pools=`cat $_pools | tail -n+3 | awk '{ print $1 }'`
        [ -z "$pools" ] || {
            echo "Error: Following pool(s)/disk-group(s) could not be deleted."
            cat $_prv_info
        }
    } || echo "no pools found"
    echo "getting disk group details..."
    _xml_obj_base="disk-groups"
    _xml_dg_plist=("name" "pool" "status" "health")
    disk_groups_get $_xml_dg_obj_base "${_xml_dg_obj_plist[@]}" > $_pools
    [ -s $_pools ] && {
        dgs=`cat $_pools | tail -n+3 | awk '{ print $1 }'`
        [ -z "$dgs" ] || {
            echo "Error: Following pool(s)/disk-group(s) could not be deleted."
            cat $_prv_info
        }
    }
    rm -rf $_pools $_prv_info
}

is_system_clean()
{
    echo "is_system_clean(): Entry" >> $logfile
    _prv_info="$tmpdir/provisioning_info"
    [ -f $_prv_info ] && rm -rf $_prv_info
    provisioning_info_get > $_prv_info
    [ -s $_prv_info ] && {
        echo -e "Error: The storage controller is not in clean state\n"
        echo "Following pool(s)/disk-group(s) are currently provisioned"
        cat $_prv_info
        echo -e "\nPlease remove the above provisioning mannually and try again"
        echo "Or Rerun the command with -c|--cleanup option"
        rm -rf $_prv_info
        return 1
    } || echo "is_system_clean(): System is in clean state" >> $logfile
    rm -rf $_prv_info
    return 0
}

disk_group_add()
{
    _type=$1
    _level=$2
    _drange=$3
    _pool_name=$4

    echo "disk_group_add(): Entry" >> $logfile
    [ $_type = "virtual" ] && {
        [ "$_pool_name" != "a" -a "$_pool_name" != "b" ] && {
            echo "Error: Invalid virtual pool name provided- $_pool_name,"\
                 " virtual pool can either be a or b"
            exit 1
        }
        _pool_opts="pool $_pool_name"
    } || {
        _pool_opts="$_pool_name"
        [ "$_pool_opts" = "" ] && {
            echo "Error: Invalid linear disk-group name provided"
            exit 1
        }
    }

    _cmd_opts="type $_type disks $_drange level $_level $_pool_opts"
    _cmd="add disk-group $_cmd_opts"
    echo "disk_group_add(): running command: '$_cmd'" >> $logfile
    echo "Creating $_type pool '$_pool_name' with $_level level"\
         "over $_drange disks"
    cmd_run "$_cmd"
}

pools_info_get()
{
    _bt=$1
    shift
    _pl=("$@")
    _tmp_file="$tmpdir/sps"
    _pools="$tmpdir/pools_info"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    [ -f $_pools ] && rm -rf $_pools

    _cmd="show pools"
    echo "pools_info_get(): Entry" >> $logfile
    echo "pools_info_get(): running command: '$_cmd'" >> $logfile
    cmd_run "$_cmd" 
    parse_xml $xml_doc $_bt "${_pl[@]}" > $_tmp_file
    [ -s $_tmp_file ] || {
        echo "pools_info_get(): No pools found on the controller" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    echo "pools_info_get(): --------- pools -------" >> $logfile
    cat $_tmp_file >> $logfile
    echo "pools_info_get(): ---------------------" >> $logfile
    printf '%s'"--------------------- Pools -----------------------\n" > $_pools
    printf '%-15s' "${_pl[@]}" >> $_pools
    printf '\n' >> $_pools
    while IFS=' ' read -r line
    do
       arr=($line)
       printf '%-15s' "${arr[@]}" >> $_pools
       printf '\n' >> $_pools
    done < $_tmp_file
    cat $_pools
}

disk_groups_get()
{
   _bt=$1
    shift
    _pl=("$@")
    _tmp_file="$tmpdir/tdgs"
    _dgs="$tmpdir/dg_info"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    [ -f $_dgs ] && rm -rf $_dgs

    _cmd="show disk-groups"
    echo "disk_groups_get(): Entry" >> $logfile
    echo "disk_groups_get(): running command: '$_cmd'" >> $logfile
    # run command to get the pools
    cmd_run "$_cmd"
    # parse xml to get required values of properties
    parse_xml $xml_doc $_bt "${_pl[@]}" > $_tmp_file
    echo "disks_group_get(): Checking and printing the $_tmp_file" >> $logfile
    [ -s $_tmp_file ] || {
        echo "disks_group_get(): No disk-groups found on the"\
            "controller" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    echo "disks_group_get(): --------- dgs -------" >> $logfile
    cat $_tmp_file >> $logfile
    echo "disks_group_get(): ---------------------" >> $logfile
    printf '%s'"------------------- Disk-groups -------------------\n" > $_dgs
    printf '%-15s' "${_pl[@]}" >> $_dgs
    printf '\n' >> $_dgs
    while IFS=' ' read -r line
    do
       arr=($line)
       printf '%-15s' "${arr[@]}" >> $_dgs
       printf '\n' >> $_dgs
    done < $_tmp_file
    cat $_dgs
}

volumes_get()
{
   _bt=$1
    shift
    _pl=("$@")
    _tmp_file="$tmpdir/tmpvols"
    _vols="$tmpdir/vols_info"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    [ -f $_dgs ] && rm -rf $_dgs

    _cmd="show volumes"
    echo "volumes_get(): Entry" >> $logfile
    echo "volumes_get(): running command: '$_cmd'" >> $logfile
    # run command to get the pools
    cmd_run "$_cmd"
    # parse xml to get required values of properties
    parse_xml $xml_doc $_bt "${_pl[@]}" > $_tmp_file
    echo "volumes_get(): Checking parsed output" >> $logfile
    [ -s $_tmp_file ] || {
        echo "volumes_get(): No volumes found on the controller" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    echo "volumes_get(): Getting vols details" >> $logfile
    echo "volumes_get(): --------- volumes -------" >> $logfile
    cat $_tmp_file >> $logfile
    echo "volumes_get(): ---------------------" >> $logfile
    printf '%s'"------------------- Volumes -----------------------\n" > $_vols
    printf '%-20s' "${_pl[@]}" >> $_vols
    printf '\n' >> $_vols
    while IFS=' ' read -r line
    do
       arr=($line)
       printf '%-20s' "${arr[@]}" >> $_vols
       printf '\n' >> $_vols
    done < $_tmp_file
    cat $_vols
}

disks_info_get()
{
    _bt=$1
    shift
    _pl=("$@")
    _tmp_file="$tmpdir/tmpdisks"
    _disks="$tmpdir/disks_info"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    [ -f $_disks ] && rm -rf $_disks

    _cmd="show disks"
    echo "disks_get(): Entry" >> $logfile
    echo "disks_get(): running command: $_cmd" >> $logfile
    # run command to get the disks
    cmd_run "$_cmd"
    # parse xml to get required values of properties
    parse_xml $xml_doc $_bt "${_pl[@]}" > $_tmp_file
    echo "disks_get(): Checking parsed output" >> $logfile
    [ -s $_tmp_file ] || {
        echo "disks_get(): No disks found on the controller" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    echo "disks_get(): Getting disks details" >> $logfile
    echo "disks_get(): --------- disks -------" >> $logfile
    cat $_tmp_file >> $logfile
    echo "disks_get(): ---------------------" >> $logfile
    printf '%s'"------------------- Disks -----------------------\n" > $_disks
    printf '%-15s' "${_pl[@]}" >> $_disks
    printf '\n' >> $_disks
    while IFS=' ' read -r line
    do
       arr=($line)
       echo "disks_info_get(): arr:$arr" >> $logfile
       printf '%-15s' "${arr[@]}" >> $_disks
       printf '\n' >> $_disks
    done < $_tmp_file
    cat $_disks 
}

disks_show_all()
{
    echo "disks_show_all(): Entry" >> $logfile
    _dsk="$tmpdir/disks"
    _xml_dsk_obj_base="drives"
    _xml_dsk_obj_plist=("slot" "location" "disk-group" "status" "health")
    [ -f "$_dsk" ] && rm -rf "$_dsk"
    disks_info_get $_xml_dsk_obj_base "${_xml_dsk_obj_plist[@]}" >> $_dsk
    [ -s $_dsk ] || {
        echo "disks_show_all(): No disks data found" >> $logfile
        return 0
    }
    cat $_dsk
}

disks_range_get()
{
    _dsk="$tmpdir/disks"
    _range1="$tmpdir/r1"
    _range2="$tmpdir/r2"
    _xml_dsk_obj_base="drives"
    _xml_dsk_obj_plist=("slot" "location" "disk-group" "status" "health")
    [ -f "$_dsk" ] && rm -rf "$_dsk"
    echo "disks_range_get(): Getting disks ranges" >> $logfile
    disks_info_get $_xml_dsk_obj_base "${_xml_dsk_obj_plist[@]}" > $_dsk
    [ -s $_dsk ] || {
        echo "disks_range_get(): No disks data found" >> $logfile
        return 0
    }
    
    echo "disks_range_get(): Checking free/available disks" >> $logfile
    ndisks=`cat $_dsk | grep "N/A"| grep "Up" | grep "OK" | wc -l`
    ndisks1=$(( ndisks/2 ))
    ndisks2=$(( ndisks1 + 1 ))
    echo "disks_range_get(): ndisks:$ndisks, ndisks1:$ndisks1,"\
        "ndisks2:$ndisks2" >> $logfile
    cat $_dsk | grep "N/A"| grep "Up" | grep "OK" | awk '{ print $1 }'\
        | head -n +$ndisks1 > $_range1
    cat $_dsk | grep "N/A"| grep "Up" | grep "OK" | awk '{ print $1 }'\
        | tail -n +$ndisks2 > $_range2
    #convert the ranges in to csv 
    echo "disks_range_get(): Converting the disk no to csv" >> $logfile
    ndisks=`cat $_dsk | grep "N/A"| grep "Up" | grep "OK" | wc -l`
    r1csv=`paste -d, -s $_range1`
    r2csv=`paste -d, -s $_range2`
    echo "disks_range_get(): r1cvs:$r1csv, r2csv:$r2csv">> $logfile
    __range1=`awk -F',' '{
        x = nxt = 0;
        for (i=1; i<=NF; i++)
        if ($i+1 == $(i+1)) { if (!x) x = $i"-"; nxt = $(i+1) }
        else { printf "%s%s", (x)? x nxt : $i, (i == NF)? ORS : FS; x = 0 }
        }'<<< "$r1csv"`
    __range2=`awk -F',' '{
        x = nxt = 0;
        for (i=1; i<=NF; i++)
        if ($i+1 == $(i+1)) { if (!x) x = $i"-"; nxt = $(i+1) }
        else { printf "%s%s", (x)? x nxt : $i, (i == NF)? ORS : FS; x = 0 }
        }'<<< "$r2csv"`
    range1=`echo $__range1 | sed 's/[^,]* */0.&/g'`
    range2=`echo $__range2 | sed 's/[^,]* */0.&/g'`
    echo "__range_1:$__range1, __range_2:$__range2" >> $logfile
    echo "range_1:$range1, range_2:$range2" >> $logfile
}

provisioning_info_get()
{
    _prv_all="$tmpdir/provisioning"
    _xml_dg_obj_base="disk-groups"
    _xml_dg_obj_plist=("name" "pool" "status" "health")
    _xml_obj_base="pools"
    _xml_obj_plist=("name" "health")
    _xml_vol_obj_base="volumes"
    _xml_vol_obj_plist=("volume-name" "size" "owner" "storage-pool-name" "health")
    [ -f "$_prv_all" ] && rm -rf "$prv_all"
    echo "provisioning_info_get(): Entry" >> $logfile
    pools_info_get $_xml_obj_base "${_xml_obj_plist[@]}" > $_prv_all
    disk_groups_get $_xml_dg_obj_base "${_xml_dg_obj_plist[@]}" >> $_prv_all
    volumes_get $_xml_vol_obj_base "${_xml_vol_obj_plist[@]}" >> $_prv_all
    [ -s $_prv_all ] || {
        echo "provisioning_info_get(): No provisioning data found" >> $logfile
        return 0
    }
    cat $_prv_all
}

remove_dg()
{
    _dg=$1
    _cmd="remove disk-group $_dg"
    echo "remove_dg(): Entry" >> $logfile
    echo "remove_dg(): running command '$_cmd'" >> $logfile

    cmd_run "$_cmd" > $xml_doc
    cli_status_get $xml_doc
}

remove_pool()
{
    _pool=$1
    _cmd="delete pools $_pool"
    echo "remove_pool(): Entry" >> $logfile
    echo "remove_pool(): running command '$_cmd'" >> $logfile
    cmd_run "$_cmd" > $xml_doc
    cli_status_get $xml_doc
}


convert_to_bytes()
{
    _avail_size=$1
    _kb=1000
    _mb=$_kb*$_kb
    _gb=$_mb*$_kb
    _tb=$_gb*$_kb
    _pb=$_tb*$_kb

    [ -z "$_avail_size" ] && {
        echo "convert_to_bytes(): Error: invalid input received"
        exit 1
    }
    _avail_size_unit=`echo $_avail_size | tr -dc 'A-Z'`
    _avail_size_val=`echo $_avail_size | sed 's/[^0-9.]*//g'`

    echo "convert_to_bytes(): _avail_size: $_avail_size" >> $logfile
    case $_avail_size_unit in
        B)
          _size_bytes=$_avail_size
          ;;
        KB)
          _size_bytes=`bc <<< $_avail_size_val*$_kb`
          ;;
        MB)
          _size_bytes=`bc <<< $_avail_size_val*$_mb`
          ;;
        GB)
          _size_bytes=`bc <<< $_avail_size_val*$_gb`
          ;;
        TB)
          _size_bytes=`bc <<< $_avail_size_val*$_tb`
          ;;
        PB)
          _size_bytes=`bc <<< $_avail_size_val*$_pb`
          ;;
    esac
    # get rid of the decimal points from the size in byte
    bsize=`echo $_size_bytes | cut -d'.' -f1`
    echo "convert_to_bytes(): $_avail_size in bytes: $bsize" >> $logfile
    echo $bsize
}

convert_from_bytes()
{
    _bytes=$1
    _tgt_unit=$2
    _kb=1000
    _mb=$_kb*$_kb
    _gb=$_mb*$_kb
    _tb=$_gb*$_kb
    _pb=$_tb*$_kb

    [ -z "$_bytes" -o -z "$_tgt_unit" ] && {
        echo "convert_from_bytes(): Error: invalid input received"
        exit 1
    }
    echo "convert_from_bytes():$_bytes to $_tgt_unit" >> $logfile
    case $_tgt_unit in
        KB)
          _tgt_usize=`bc -l <<< "scale=2; $_bytes/$(bc <<< $_kb)"`
          ;;
        MB)
          _tgt_usize=`bc -l <<< "scale=2; $_bytes/$(bc <<< $_mb)"`
          ;;
        GB)
          _tgt_usize=`bc -l <<< "scale=2; $_bytes/$(bc <<< $_gb)"`
          ;;
        TB)
          _tgt_usize=`bc -l <<< "scale=2; $_bytes/$(bc <<< $_tb)"`
          ;;
        PB)
          _tgt_usize=`bc -l <<< "scale=2; $_bytes/$(bc <<< $_pb)"`
          ;;
        *)
          echo "convert_from_bytes(): Eror: Invalid unit specified"
          exit 1
          ;;
    esac
    _tgt_usize=`printf "%.2f" "$_tgt_usize"`
    _tgt_usize="${_tgt_usize}$_tgt_unit"
    echo "convert_from_bytes(): $_bytes to $_tgt_unit: $_tgt_usize" >> $logfile
    echo $_tgt_usize
}

vol_size_get()
{
    _avail_size=$1
    _nvols=$2
    _avail_size_unit=`echo $_avail_size | tr -dc 'A-Z'`
    _bytes_avlblsize=`convert_to_bytes $_avail_size`
    _bytes_200mb=`convert_to_bytes 200MB`
    _bytes_2g=`convert_to_bytes 2GB`
    _bytes_24g=`convert_to_bytes 24GB`

    echo "vol_size_get(): avail_size:$_avail_size,"\
        "volumes to be created:$_nvols" >> $logfile
    [ $_bytes_avlblsize -lt $_bytes_200mb ] && {
        echo "Error: Insufficient pool size available:"\
            "`convert_from_bytes $_bytes_avlblsize MB`, exiting";
        exit 1
    }
    _new_size_in_bytes=$(( _bytes_avlblsize - _bytes_24g ))
    _volsize=`bc <<< $_new_size_in_bytes/$_nvols`
    echo "vol_size_get(): new size after 8gb less:"\
        "`convert_from_bytes $_new_size_in_bytes GB`" >> $logfile
    echo "vol_size_get()"\
        "_volsize:`convert_from_bytes $_volsize GB`($_volsize)" >> $logfile
    [ $_volsize -lt $_bytes_2g ] && {
        echo -e "Error: Volume of size less than 2GB is not supported in CORTX" 
        echo -e "Error: Insufficient space($_avail_size)"\
            "available in pool to create"\
                "$_nvols volumes of size of at least 2GB."
        return 1
    } 
    vsize=`convert_from_bytes $_volsize GB`
    echo "vol_size_get(): volsize:$vsize" >> $logfile
    return 0
}

base_lun_get()
{
    _luns="$tmpdir/luns"
    _bt="volume-view-mappings"
    _pl=("lun")
    _cmd="show volume-maps"

    echo "base_lun_get(): running command '$_cmd'" >> $logfile
    cmd_run "$_cmd"
    parse_xml $xml_doc $_bt "${_pl[@]}" > $_luns
    echo "base_lun_get(): -------- luns -------" >> $logfile
    cat $_luns >> $logfile
    echo "base_lun_get(): ---------------------" >> $logfile
    base_lun=`cat $_luns | grep -v "N/A" | sort -n | tail -1`
    base_lun=$((base_lun+1))
    echo $base_lun >> $logfile
    echo $base_lun
}

volumes_create()
{
    _blun="$1"
    _nvols="$2"
    _pool_name="$3"
    _pool_opt="pool $_pool_name"
    _size_opt="size $4"
    _ports_opt="ports $5"

    if [[ "$_blun" == "9" ]]
    then
      _mylun="0"
    fi

    _mylun=$((_mylun+1))
    _vol_name="${_pool_name}-v000${_mylun}"

    _cmd="create volume"
    _cmd_opts="access read-write $_pool_opt $_size_opt $_ports_opt"
    _vol_create_cmd="${_cmd} $_vol_name $_cmd_opts lun $_blun"
    echo "create volume lun: $_blun,"\
      " pool-name: $3, vsize: $4, ports: $5" >> $logfile
    echo "Creating volume $_vol_name of $_size_opt in"\
      "$_pool_opt mapped to $_ports_opt"
    cmd_run "$_vol_create_cmd"

    #TODO: Confirm if volume-set created successfully
}

# Provision the cluster
# input parameters
# _pool_type : Type of the pool to be created e.g. virtual or linear
# _level : pool level - adapt, r6 etc.
# _nvols : no of volumes to be created per pool, default 8
# _drange: disk range where the pool to be created over
# _pool_name : pool name
# 
# e.g.
# provision linear adapt 8 0.0-15 dg01
# provision virtual adapt 8 0.16-31 a/b
provision()
{
    _pool_type=$1
    _level=$2
    _nvols=$3
    _drange=$4
    _pool_name=$5
    _pools_info=$tmpdir/prv_pinfo
    
    [ -z "$_pool_type" -o -z "$_level" -o -z "$_nvols" -o \
        -z "$_drange" -o -z "$_pool_name" ] && {
        echo "Error: provision(): Invalid inputs received for provisioning"
        rm -rf $tmpdir
        exit 1
    }
    echo "provision(): pool-type:$1,level:$2,nvols:$3,disks:$4,"\
        "pool-name:$5" >> $logfile
    [ "$_pool_type" != "virtual" -a "$_pool_type" != "linear" ] && {
        echo "Error: Invalid pool type provided- $_pool_type, only virtual"\
             " and linear pool types are supported."
        rm -rf $tmpdir
        exit 1
    }

    # Add the disk group
    echo "provision(): creating $_pool_type pool/disk"\
        "group:$_pool_name" >> $logfile
    disk_group_add $_pool_type $_level $_drange $_pool_name

    # Get pool status to check pool size and health
    # Prepare arguments to be extracted from xml 
    _xml_obj_base="pools"
    _xml_obj_plist=("name" "total-size" "total-avail" "health")

    pools_info_get $_xml_obj_base "${_xml_obj_plist[@]}" > $_pools_info
    [ -s $_pools_info ] || {
        echo "Error: pool $_pool_name doesn't exist"
        rm -rf $_pools_info
        return 1
    }
    cat $_pools_info >> $logfile
    _pool_status=`cat $_pools_info | grep $_pool_name | awk '{ print $4 }'`
    [ "$_pool_status" = "OK" ] && {
        echo "Pool $_pool_name Created Successfully"
    } || {
        echo "Error: Pool $pool_name is not in good health, exiting";
        rm -rf $tmpdir
        exit 1
    }

    # Extract total space available  on the created pool
    _total_space=`cat $_pools_info | grep $_pool_name | awk '{ print $2 }'`
    _avail_space=`cat $_pools_info | grep $_pool_name | awk '{ print $3 }'`
    _avail_space_bytes=`convert_to_bytes $_avail_space`
    _avail_space_gb=`convert_from_bytes $_avail_space_bytes 'GB'`
    echo "provision(): total space in pool:$_total_space" >> $logfile
    echo "provision(): avail space in pool:$_avail_space" >> $logfile
    echo "provision(): avail space(gb) in pool:$_avail_space_gb" >> $logfile
    # Derive size of the volumes to be created
    vsize=0
    vol_size_get $_avail_space_gb $_nvols
    ret=$?
    [ $ret -ne 0 -o `convert_to_bytes $vsize` -eq 0 ] && {
        echo "Provision(): Error: exiting"
        rm -rf $tmpdir
        exit 1
    }
    echo "provision(): vol size:$vsize, nvols:$_nvols" >> $logfile

    #get all the UP ports on the controller, the volumes will be
    #mapped to all the ports.
    _ports=`active_ports_get`
    echo "provision(): active port list:$_ports" >> $logfile

    for (( _myvol=1; _myvol<=$_nvols; _myvol++ ))
    do
      #Get base lun number, it is the next available lun number in the system.
      _baselun=`base_lun_get`
      echo "provision(): baselun: $_baselun; nvol: $_nvols; pool_name: $_pool_name" >> $logfile

      #create volumes and map them to all the ports
      echo "provision(): Creating volumes" >> $logfile
      volumes_create $_baselun $_nvols $_pool_name $vsize $_ports
    done
}

fw_ver_get()
{
    _tmp_file="$tmpdir/tmp_fw_ver"
    [ -f "$_tmp_file" ] && rm -rf "$_tmp_file"
    _fw_ver="$tmpdir/fw_ver"
    [ -f "$_fw_ver" ] && rm -rf "$_fw_ver"
    echo "fw_ver_get(): Entry" >> $logfile
    _xml_obj_bt="versions"
    _xml_obj_plist=("bundle-version")
    _cmd="show configuration"

    echo "fw_ver_get(): running command: $_cmd" >> $logfile
    cmd_run "$_cmd"
    parse_xml $xml_doc $_xml_obj_bt "${_xml_obj_plist[@]}" > $_tmp_file
    [ -s $_tmp_file ] || {
        echo "fw_ver_get(): Couldn't get the firmware version" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    printf '%s'"fw_ver_get() Firmware version\n" > $_fw_ver
    cat $_tmp_file >> $logfile
    printf '%s'"--------------------- Firmware Version -----------------------\n" > $_fw_ver
    printf '%-15s' "${_xml_obj_plist[@]}" >> $_fw_ver
    printf '\n' >> $_fw_ver
    while IFS=' ' read -r line
    do
       arr=($line)
       printf '%-15s' "${arr[@]}" >> $_fw_ver
       printf '\n' >> $_fw_ver
    done < $_tmp_file
    controller_A_ver=$(cat $_fw_ver | grep -A1 bundle-version | tail -1 | xargs)
    controller_B_ver=$(cat $_fw_ver | grep -A2 bundle-version | tail -1 | xargs)
    cat $_fw_ver
}

midplane_serial_get()
{
    _tmp_file="$tmpdir/tmp_serial"
    [ -f "$_tmp_file" ] && rm -rf "$_tmp_file"
    _mp_serial="$tmpdir/mp_serial"
    [ -f "$_mp_serial" ] && rm -rf "$_mp_serial"
    echo "midplane_serial_get(): Entry" >> $logfile
    _xml_obj_bt="system"
    _xml_obj_plist=("midplane-serial-number")
    _cmd="show system"

    echo "midplane_serial_get(): running command: $_cmd" >> $logfile
    cmd_run "$_cmd"
    parse_xml $xml_doc $_xml_obj_bt "${_xml_obj_plist[@]}" > $_tmp_file
    [ -s $_tmp_file ] || {
        echo "midplane_serial_get(): Couldn't get the midplane serial " >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    printf '%s'"midplane_seria_get() Serial number\n" > $_mp_serial
    cat $_tmp_file >> $logfile
    printf '%s'"--------------------- Serial number-----------------------\n" > $_mp_serial
    printf '%-15s' "${_xml_obj_plist[@]}" >> $_mp_serial
    printf '\n' >> $_mp_serial
    while IFS=' ' read -r line
    do
       arr=($line)
       printf '%-15s' "${arr[@]}" >> $_mp_serial
       printf '\n' >> $_mp_serial
    done < $_tmp_file
    cat $_mp_serial
}

sc_license_get()
{
    _tmp_file="$tmpdir/license-details"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    # objects name in the xml
    _xml_obj_bt="license"
    _xml_obj_plist=("virtualization" "volume-copy" "remote-snapshot-replication"\
    "vds" "vss" "sra")
    echo "sc_license_get(): Getting licenses "${_xml_obj_plist[@]}"" >> $logfile

    # run command to get the license details
    _cmd="show license"
    echo "Getting license details.." >> $logfile
    echo "sc_license_get(): Running command: '$_cmd'" >> $logfile
    cmd_run "$_cmd"
    # parse xml to get required values of properties
    parse_xml $xml_doc $_xml_obj_bt "${_xml_obj_plist[@]}" > $_tmp_file
    [ -s $_tmp_file ] || {
        echo "sc_license_get(): No licenses found on the controller" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    echo "------licenses---------" >> $logfile
    cat $_tmp_file >> $logfile
    echo "-----------------------" >> $logfile
    printf '%s'"--------------------- licenses ---------------------\n"
    declare -a license_details
    license_details=(`cat "$_tmp_file"`)
    for ((i=0; i<=${#_xml_obj_plist[@]}; i++)); do
        printf '%-28s %s\n' "${_xml_obj_plist[i]}" "${license_details[i]}"
    done
}

pkg_install()
{
    _pkg="$1"
    echo "Installing $_pkg"
    yum install -q -y $_pkg > /dev/null 2>&1
    ret=$?
    [ $ret -eq 0 ] || {
        echo "Error installing $_pkg"
        exit 1
    }
    echo "pkg_install(): $_pkg installed successfully" >> $logfile
}

reqd_pkgs_install()
{
    for pkg in "$@"; do
        pkg_name=$(basename $pkg)
        [ -f "$pkg" ] || {
            echo "reqd_pkgs_install(): $pkg_name not installed " >> $logfile
            #pkg_install $pkg_name
            echo "ERROR: $pkg_name is not installed" | tee -a $logfile
            echo "Please make sure $pkg_name is installed before running the command" | tee -a $logfile
            exit 1
        }
    done
}

ftp_cmd_run()
{
    _cmd="$1"
    _ftp_op=
    ftp_cmd="/bin/ftp"

    if echo $_cmd | grep -q flash; then
        _ftp_op="Firmware Update"
    else
        _ftp_op="License load"
    fi

    echo "ftp_cmd_un(): _ftp_op=$_ftp_op" >> $logfile

    if [ -f $ftp_log ]; then
        ts=$(date +"%Y-%m-%d_%H-%M-%S")
        yes | cp -f $ftp_log ${logdir}/fw_upgrade_${ts}.log
    fi

    echo "ftp_cmd_run(): cmd: $_cmd" >> $logfile
    reqd_pkgs_install $ftp_cmd
    echo "ftp_cmd_run(): starting ftp session" >> $logfile
$ftp_cmd -inv $host > $ftp_log  <<EOF &
user $user "$pass"
$_cmd
bye
EOF

ftp_pid=$!
echo "ftp PID:$ftp_pid" >> $logfile
_sleep_time=30
_max_ntry=120
_ntry=0

until ! ps -aef | grep $ftp_pid | grep -v grep > /dev/null; do
    echo "ftp_cmd_run(): _ntry:$_ntry, _max_ntry:$_max_ntry" >> $logfile
    if [[ $_ntry -eq $_max_ntry ]]; then
        echo "$_ftp_op did not complete after 60 minutes" >> $logfile
        ftp_op_timeout=true
        break
    else
        echo "$_ftp_op is in progress, please wait, check the $ftp_log for progress..." | tee -a $logfile
        sleep $_sleep_time
        _ntry=$(( _ntry + 1 ))
    fi
done

_ntry=0
_sleep_time=2
_max_ntry=2
#Hack to not print the output of kill -9 on the std output
disown $ftp_pid

until ! ps -aef | grep $ftp_pid | grep -v grep > /dev/null; do
    echo "ftp_cmd_run(): _ntry:$_ntry, _max_ntry:$_max_ntry" >> $logfile
    if [[ $_ntry -eq $_max_ntry ]]; then
        echo "Could not kill ftp session (PID:$ftp_pid) after $_max_ntry attempts" >> $logfile
        ftp_kill_timeout=true
        break
    else
        echo "Killing the ftp session(PID:$ftp_pid)" >> $logfile
        kill -9 $ftp_pid 2>&1 | tee -a $logfile
        sleep $_sleep_time
        _ntry=$(( _ntry + 1 ))
    fi
done

}

fw_license_load()
{
    echo "Loading the license"
    [ -z $license_file ] && echo "Error: No firmware bundle provided" &&
        exit 1
    ftp_cmd_run "put $license_file license"
}

is_ftp_enabled()
{
    _tmp_file="$tmpdir/is_ftp_enabled"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    # objects name in the xml
    _xml_obj_bt="security-communications-protocols"
    _xml_obj_plist=("ftp")
    # run command to get the details of advanced settings params
    echo "is_ftp_enabled():Getting protocols details.." >> $logfile
    _cmd="show protocols"
    cmd_run "$_cmd"
    echo "is_ftp_enabled():Checking if ftp is enabled" >> $logfile

    # parse xml to get required values of properties
    parse_xml $xml_doc $_xml_obj_bt "${_xml_obj_plist[@]}" > $_tmp_file
    [ -s $_tmp_file ] || {
        echo "is_ftp_enabled(): No ftp setting found" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    ret=$(grep -q "Enabled" $_tmp_file)
    if [[ $ret -eq 0 ]]; then
        echo "Enabled"
    else
        echo "Disabled"
    fi
}

ftp_enable()
{
    _tmp_file="$tmpdir/ftp_enable"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    echo "ftp_enable(): Checking if ftp is enabled" >> $logfile
    is_ftp_enabled > $_tmp_file
    grep -q "Enabled" $_tmp_file || {
        echo "ftp_enable(): ftp disabled, enabling ftp" >> $logfile
        _cmd="set protocols ftp on"
        cmd_run "$_cmd"
        is_ftp_enabled > $_tmp_file
        echo "ftp_enable(): Checking if ftp got enabled" >> $logfile
        grep -q "Enabled" $_tmp_file || {
           echo "ftp_enable(): Error: Could not enable ftp"
           exit 1
        }
    } && echo "ftp_enable(): ftp is already enabled" >> $logfile
}

# Check if sftp service is enabled on controller
is_sftp_enabled()
{
    _ret=1
    _tmp_file="$tmpdir/is_sftp_enabled"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    # objects name in the xml
    _xml_obj_bt="security-communications-protocols"
    _xml_obj_plist=("sftp")
    # run command to get the details of advanced settings params
    echo "is_sftp_enabled():Getting protocols details.." >> $logfile
    _cmd="show protocols"
    cmd_run "$_cmd"
    echo "is_sftp_enabled():Checking if sftp service is enabled" >> $logfile

    # parse xml to get required values of properties
    parse_xml $xml_doc $_xml_obj_bt "${_xml_obj_plist[@]}" > $_tmp_file
    [ -s $_tmp_file ] || {
        echo "is_sftp_enabled(): No sftp setting found" >> $logfile
        rm -rf $_tmp_file
        exit 1
    }
    grep -q "Enabled" $_tmp_file && _ret=0
    echo "is_sftp_enabled(): _ret=$_ret" >> $logfile
    return $_ret
}

# Enable the sftp service on the controller.
sftp_enable()
{
    _tmp_file="$tmpdir/sftp_enable"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    echo "sftp_enable(): Checking if sftp service is enabled" >> $logfile
    is_sftp_enabled || {
        echo "ERROR: The sftp service is not enabled on the controller, please enable it manually and run the command again!!" | tee -a $logfile
        exit 1
        # TODO: Following code doesn't work find a way to enable sftp through shell script
            # echo "sftp_enable(): sftp is disabled, enabling sftp" >> $logfile
            # _cmd="set protocols sftp enable"
            # cmd_run "$_cmd"
            # echo "sftp_enable(): Checking again if sftp got enabled now" >> $logfile
            # is_sftp_enabled || {
            #    echo "sftp_enable(): Error: Could not enable sftp service"
            #    exit 1
            # } && echo "sftp_enable(): sftp service is now enabled" >> $logfile
    } && echo "sftp_enable(): sftp service is already enabled" >> $logfile
}

is_pfu_enabled()
{
    _tmp_file="$tmpdir/is_pfu_enabled"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    # objects name in the xml
    _xml_obj_bt="advanced-settings-table"
    _xml_obj_plist=("partner-firmware-upgrade")
    # run command to get the details of advanced settings params
    echo "Getting advanced setting details.." >> $logfile
    _cmd="show advanced-settings"
    cmd_run "$_cmd"
    echo "Checking if pfu is enabled" >> $logfile

    # parse xml to get required values of properties
    parse_xml $xml_doc $_xml_obj_bt "${_xml_obj_plist[@]}" > $_tmp_file
    [ -s $_tmp_file ] || {
        echo "is_pfu_enabled(): No pfu setting found" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    ret=$(grep -q "Enabled" $_tmp_file)
    if [[ $ret -eq 0 ]]; then
        echo "Enabled"
    else
        echo "Disabled"
    fi
}

pfu_enable()
{
    _tmp_file="$tmpdir/pfu_enable"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    echo "pfu_enable(): Checking if PFU is enabled" >> $logfile
    is_pfu_enabled > $_tmp_file
    grep -q "Enabled" $_tmp_file || {
        echo "pfu_enable(): PFU disabled, enabling PFU" >> $logfile
        _cmd="set advanced-settings partner-firmware-upgrade on"
        cmd_run "$_cmd"
        is_pfu_enabled > $_tmp_file
        echo "pfu_enable(): Checking if PFU got enabled" >> $logfile
        grep -q "Enabled" $_tmp_file || {
           echo "pfu_enable(): Error: Could not enable PFU"
           exit 1
        }
    } && echo "pfu_enable(): PFU is already enabled" >> $logfile
}

fw_upgrade_health_check()
{
    _tmp_file="$tmpdir/fw_upgrade_health_check"
    [ -f $_tmp_file ] && rm -rf $_tmp_file
    # objects name in the xml
    _xml_obj_bt="code-load-readiness"
    _xml_obj_plist=("overall-health")
    # run command to get the details of advanced settings params
    echo "fw_upgrade_health_check():Getting upgrade health status" >> $logfile
    _cmd="check firmware-upgrade-health"
    cmd_run "$_cmd"
    echo "fw_upgrade_health_check():Checking if health is ok" >> $logfile

    # parse xml to get required values of properties
    parse_xml $xml_doc $_xml_obj_bt "${_xml_obj_plist[@]}" > $_tmp_file
    [ -s $_tmp_file ] || {
        echo "fw_upgrade_health_check(): No status found" >> $logfile
        rm -rf $_tmp_file
        return 0
    }
    grep -q "Pass" $_tmp_file && {
        echo "fw_upgrade_health_check():Pass" >> $logfile
    } || {
        echo "fw_upgrade_health_check():Fail" >> $logfile
        echo "Error: Controller is not in healthy state" 2>&1 | tee -a $logfile
        echo "Error: Aborting firware upgrade" 2>&1 | tee -a $logfile
        exit 1
    }
}

# Run the commands on controller over sftp
# create sftp session and run the commands
# provided in the batchfile as input to the function.
sftp_cmd_run()
{
    local _batch_file="$1"
    local _cmd=$(cat $_batch_file)
    local _scr_sleep_time=30
    local _scr_max_ntry=10
    local _scr_ntry=0
    local _scr_ret=
    local _sftp_log="$tmpdir/sftp.log"
    if [[ ! -f $_sftp_log ]]; then
        touch $_sftp_log
    fi

    if ! command  -v sftp; then
        echo "ERROR: sftp command could not be found" | tee -a $logfile
        echo "Please install sftp and try again" | tee -a $logfile
        exit 1
    fi

    while true; do
        echo "DEBUG: sftp_cmd_run(): _scr_ntry=$_scr_ntry, _scr_max_ntry=$_scr_max_ntry" >> $logfile
        if [[ $_scr_ntry -ge $_scr_max_ntry ]]; then
            echo "ERROR: Could not establish the sftp session with $host after many attempts, exiting.." | tee -a $logfile
            exit 1
        fi
        echo "DEBUG: sftp_cmd_run(): starting sftp session" >> $logfile
        echo "DEBUG: sftp_cmd_run(): Running cmd: $_cmd" >> $logfile
sshpass -p "$pass" sftp -P 1022 -oBatchMode=no -b - ${user}@${host} << EOF 2>&1 | tee $_sftp_log
$_cmd
bye
EOF
        _scr_ret=${PIPESTATUS[0]}
        # copy the sftp logs to the main sftp log file (reqd for debugging purpose)
        cat $_sftp_log >> $sftp_log
        echo "DEBUG: sftp_cmd_run(): sftp returned with exit code: $_scr_ret" >> $logfile
        if [[ $_scr_ret -ne 0 ]]; then
            if [[ $_scr_ret -eq 255 ]]; then
                #ssh error to the host, may be after the restart ssh service isn't up yet.
                # wait for some time and try again.
                echo "DEBUG: sftp_cmd_run(): ssh error, controller host may be getting rebooted, trying again in a while.." >> $logfile
                sleep $_scr_sleep_time
                _scr_ntry=$(( _scr_ntry + 1 ))
                continue
            elif grep -q 'File "/progress" not found' $_sftp_log; then
                #ignore the error 'File "/progress" not found'
                break
            else
                # Exit on all other error cases
                echo "ERROR: sftp command returned with non-zero exit code ($_scr_ret) please check $sftp_log for more details.." | tee -a $logfile
                exit $_scr_ret
            fi
        else
            break
        fi
    done
    echo "DEBUG: sftp_cmd_run() done" >> $logfile
}

# Prepare the command string to get the last code
# load status & invoke the command over sftp
fw_codeload_status_get()
{
    _sftp_cmd="get progress:lastcodeload:text $ftp_log"
    # Prepare the batch file of sftp commands to be executed over sftp.
    printf '%s\n' "$_sftp_cmd" > $tmpdir/fw_upd.bf
    echo "DEBUG: fw_codeload_status_get() _sftp_cmd=$_sftp_cmd." >> $logfile
    echo "DEBUG: fw_codeload_status_get() contents of $tmpdir/fw_upd.bf" >> $logfile
    cat $tmpdir/fw_upd.bf >> $logfile
    sftp_cmd_run "${tmpdir}/fw_upd.bf"
}

# Get the fw version from input bundle
bundle_ver_get()
{
    if [[ -z $fw_bundle || ! -f $fw_bundle ]]; then
        echo "ERROR: Invalid input bundle provided, exiting" | tee -a $logfile
        exit 1
    fi
    echo "Getting the fw version from the input bundle" >> $logfile
    _bundle_ver=$(grep -a "<BUNDLE version=" $fw_bundle | awk '{ print $2 }' | cut -d= -f 2)
    # Sample output of grep command
    # grep -a "<BUNDLE version=" GN265R009-03.bin 
    # <BUNDLE version="GN265R009-03" build_date="Wed Sep 19 13:36:08 MDT 2018" seconds="180">

    if [[ -z $_bundle_ver ]]; then
        echo "ERROR: Could not get the target fw version from the input bundle" | tee -a $logfile
        echo "ERROR: Please check if the bundle is valid" | tee -a $logfile
        exit 1
    fi
    #ver would have quotes around it, remove the quotes:
    bundle_fw_ver="${_bundle_ver%\"}" #remove quote at the end
    bundle_fw_ver="${bundle_fw_ver#\"}" # remove quote at the start

    echo "Firmware Version in the input bundle provided: $bundle_fw_ver" | tee -a $logfile
}

# Compare current versions of the ctrl fw with the
# target version and the versions before update was triggered. 

# Return value is set in variable: ret_fw_versions_compare
# Return values
# Both controller got updated: 0
# A is updated but B is not  : 1
# B is updated but A is not  : 2
# Both controller not updated: 3
fw_versions_compare()
{
    # read the fw version captured before starting the update
    #TODO: check input params are not empty
    _ctrl_a_ver_old=$1
    _ctrl_b_ver_old=$2
    ret_fw_versions_compare=99
    echo "Old firmware version:" | tee -a $logfile
    echo "Controller A: $_ctrl_a_ver_old, Controller B: $_ctrl_b_ver_old" | tee -a $logfile

    echo "Getting current fw versions on the controller" >> $logfile
    fw_ver_get >> $logfile
    echo "Current firmware version on the controller:" | tee -a $logfile
    echo "Controller A: $controller_A_ver, Controller B: $controller_B_ver" | tee -a $logfile
    _ctrl_a_ver_current=$controller_A_ver
    _ctrl_b_ver_current=$controller_B_ver
    bundle_ver_get

    echo "DEBUG: Versions before the update was triggered:" >> $logfile
    echo "Controller A: ${_ctrl_a_ver_old}, Controller B: ${_ctrl_b_ver_old}" >> $logfile
    echo "DEBUG: Target version: ${bundle_fw_ver}" >> $logfile
    echo "DEBUG: Current versions:" >> $logfile
    echo "Controller A: ${_ctrl_a_ver_current}, Controller B: ${_ctrl_b_ver_current}" >> $logfile

    # Compare versions and set the return values
    # Both controller got updated: 0
    # A is updated but B is not  : 1
    # B is updated but A is not  : 2
    # Both controller not updated: 3
    if [[ ${_ctrl_a_ver_old} != ${_ctrl_a_ver_current} && ${_ctrl_b_ver_old} != ${_ctrl_b_ver_current} ]]; then
        # both controller's current fw version doesn't match with older versions, the update
        # seems to have happened, check current version with the version of the input bundle.
        echo "DEBUG: FW versions of both the controllers are different than the older version" >> $logfile
        echo "DEBUG: Checking if the versions match with target version from the input bundle" >> $logfile
        if [[  ${bundle_fw_ver} == ${_ctrl_a_ver_current} && ${bundle_fw_ver} == ${_ctrl_b_ver_current} ]]; then
            echo "Firmware is updated successfully" | tee -a $logfile
            ret_fw_versions_compare=0
        else
            echo "DEBUG:  Firmware version is updated but it doesn't match with the target version (${bundle_fw_ver})" >> $logfile
            ret_fw_versions_compare=3
        fi
    elif [[ ${_ctrl_a_ver_old} != ${_ctrl_a_ver_current} && ${_ctrl_b_ver_old} == ${_ctrl_b_ver_current} ]]; then
        # Possibly controller A got update but controller B didn't, confirm by
        # checking fw ver on A with the target version.
        echo "DEBUG: FW version on controller A got changed but Controller B is still on the older version" >> $logfile
        echo "DEBUG: Checking if FW version on controller A matches with the target FW version" >> $logfile
        if [[ "$bundle_fw_ver" == "${_ctrl_a_ver_current}" ]]; then
            ret_fw_versions_compare=1
        else
            # Controller A is neither on the target ver nor on the older version,
            # this is unexpected, the update didn't happen, so return failure.
            echo "ERROR: Controller A is neither on the target FW version nor on the original version" | tee -a $logfile
            echo "Please contact Seagate support for further assistance. Exiting with failure." | tee -a $logfile
            ret_fw_versions_compare=3
        fi
    elif [[ ${_ctrl_a_ver_old} == ${_ctrl_a_ver_current} && ${_ctrl_b_ver_old} != ${_ctrl_b_ver_current} ]]; then
        # Possibly controller B got update but controller A didn't, confirm by
        # checking fw ver on B with the target version.
        echo "DEBUG: FW version on controller B got changed but Controller A is still on the older version" >> $logfile
        echo "DEBUG: Checking if FW version on controller B matches with the target FW version" >> $logfile
        if [[ "$bundle_fw_ver" == "${_ctrl_b_ver_current}" ]]; then
            ret_fw_versions_compare=2
        else
            # Controller B is neither on the target ver nor on the older version,
            # this is unexpected, the update didn't happen, so return failure.
            echo "ERROR: Controller B is neither on the target FW version nor on the original version" | tee -a $logfile
            echo "Please contact Seagate support for further assistance. Exiting with failure." | tee -a $logfile
            ret_fw_versions_compare=3
        fi
    elif [[ ${_ctrl_a_ver_old} == ${_ctrl_a_ver_current} && ${_ctrl_b_ver_old} == ${_ctrl_b_ver_current} ]]; then
        echo "DEBUG: FW Versions for both controllers didn't change." >> $logfile
        echo "DEBUG: Checking if versions match with the target version" >> $logfile
        if [[ "$bundle_fw_ver" == "${_ctrl_a_ver_current}" && "$bundle_fw_ver" == "${_ctrl_b_ver_current}" ]]; then
            # Target ver in bundle and the verion on controllers are same,
            # The fw update was triggered with the same version, return success.
            echo "DEBUG: Target FW version in the input bundle and the FW verion on controllers are same" >> $logfile
            ret_fw_versions_compare=0
        else
            # Both the controllers are at the same older version and does not match the
            # target version, fw update did not happen, report failure.
            echo "ERROR: Both the controllers are at the same older version." | tee -a $logfile
            echo "ERROR: The firmware update did not happen." | tee -a $logfile
            ret_fw_versions_compare=3
        fi
    fi
}

# Parse the code load status file.
fw_update_status_parse()
{
    _error=0
    echo "DEBUG: fw_update_status_parse() entry" >> $logfile
    if grep -q "Codeload completed successfully." $ftp_log; then
        # IMPORTANT: Do not change the sequence of the checks below
        if grep -q "RETURN_CODE: 8" $ftp_log; then
            echo "Found RETURN_CODE 8 in $ftp_log" >> $logfile
            _error=0
        elif grep -q "RETURN_CODE: 9" $ftp_log; then
            echo "Found RETURN_CODE 9 in $ftp_log" >> $logfile
            _error=0
        elif grep -q "Not attempted (Versions match)" $ftp_log; then
            # Target fw ver and current fw versions were same - update to same ver.
            echo "Found 'Not attempted (Versions match)' in $ftp_log" >> $logfile
            _error=0
        else
            # no RETURN CODE found in the sftp log file.
            # still return success as 'codeload completed successfully' message
            # is found in the sftp logs.
            echo "Error: No RETURN CODE Found in $ftp_log, still returning with success status..." >> $logfile
            _error=0
        fi
    elif ! grep -iE "fail|error" $ftp_log | grep -vq "230-"; then
        echo "No Codeload related message or fail/error strings in $ftp_log" >> $logfile
        _error=0
    else
        echo "No Codeload related message but found fail/error strings in $ftp_log, exiting with failure status..." >> $logfile
        _error=1
    fi
    fw_update_status=$_error
}

# Update the controller firmware over sftp protocol
# Algorithm for fw update over sftp:
# Check if controller is healthy state to do the fw update
# Enable PFU (Partner Firmware Update), this ensures the other controller gets updated too.
# Enable sftp service on controller.
# Get & save the current version of the firmware on both the controller (required for validation post update)
# while true
#   Check timeout, break if update is not done in stipulated time (1 hour, soft timeout limit).
#   Check the codeload status, if update is till in progress, wait for some more time (hard timeout).
#   if controller is reachable
#      get progress from the controller over sftp (the output wil be in xml format)
#      parse the progress xml for both the controllers, it will show the activity on both controllers
#      if activity is "none" for both the controllers
#        1. Run: "get progress:lastcodeload:text $ftp_log" to get last codeload status
#        2. Parse $ftp_log file to check if update was successful (check for return code 8)
#        3. set the update status to success and break the loop
#      if activity is not "none" for any of the controller
#        This means the update is in progress, wait and continue the loop.
#   else
#      # possibly it's getting rebooted after update.
#      # wait for some time and continue to poll the controller again
# end while
# Check the current fw versions against the bundle version & the older version on the controllers
# Check the update status and fw version and return accrodingly.

fw_update()
{
    fw_upgrade_health_check
    pfu_enable
    sftp_enable

    echo "Updating the firmware on host: $host" >> $logfile
    [ -z $fw_bundle ] && echo "Error: No firmware bundle provided" &&
        exit 1

    # Save the current version of the firmware on the controllers
    echo "Getting current fw versions (before update)" >> $logfile
    fw_ver_get >> $logfile
    echo "Firmware Version on the controller before update:" | tee -a $logfile
    echo "Controller A: $controller_A_ver, Controller B: $controller_B_ver" | tee -a $logfile

    _sftp_cmd="put $fw_bundle flash"
    if echo $controller_A_ver | grep GN265 ||
       echo $controller_B_ver | grep GN265; then
        # Workaround for known issue - FMW-42117
        # update from GN265* to GN280* fails due
        # to partner communication issue, use force keywork to bypass
        _sftp_cmd="${_sftp_cmd}:force"
    fi
    printf '%s\n' "$_sftp_cmd" > $tmpdir/fw_upd.bf
    echo "DEBUG: _sftp_cmd=$_sftp_cmd" >> $logfile
    echo "DEBUG: contents of $tmpdir/fw_upd.bf" >> $logfile
    cat $tmpdir/fw_upd.bf >> $logfile

    sftp_cmd_run "${tmpdir}/fw_upd.bf"

    _sleep_time=120
    _max_ntry=30
    _max_ntry_topup=5 # hard limit for timeout - additional 10 minutes
    _hard_timeout=$(( _max_ntry + _max_ntry_topup ))
    _ntry=0
    _sftp_timedout=false
    wait_till_hard_timeout=false
    _ctrl_reachable=false
    while true; do
        echo "fw_update(): _ntry:$_ntry, _max_ntry:$_max_ntry" >> $logfile
        if [[ $_ntry -ge $_max_ntry ]]; then
            # update process didn't complete within the timeout limit.
            # Check if update is still in progress, if yes, wait for 
            # some time more until _max_ntry_hard_timeout limit is reached.
            # get the current activity on the controller
            if [[ "$_ctrl_reachable" == true ]]; then
                ctrl_activity_get "$tmpdir/progress"
                if [[ $ctrl_activity_a == "codeload" ]]; then
                    #TODO: also check the "done" status from the output of "get progress" xml file
                    # if [[ $ctrl_activity_a == "codeload" && $ctrl_a_done_status == "false" ]]; then
                    # codeload is still in progress on A, wait till hard timeout is reached.
                    echo "DEBUG: fw_update() Timeout!! But codeload is still in progress on Controller A" >> $logfile
                    wait_till_hard_timeout=true
                elif [[ $ctrl_activity_b == "codeload" ]]; then
                    #TODO: also check the "done" status from the output of "get progress" xml file
                    # elif [[ $ctrl_activity_b == "codeload" && $ctrl_b_done_status == "false" ]]; then
                    # codeload is still in progress on B, wait till hard timeout is reached.
                    echo "DEBUG: fw_update() Timeout!! But codeload is still in progress on Controller B" >> $logfile
                    wait_till_hard_timeout=true
                else
                    # set the wait_till_hard_timeout to false
                    wait_till_hard_timeout=false
                fi
            fi
            if [[ "$wait_till_hard_timeout" == true ]]; then
                if [[ $_ntry -ge $_hard_timeout ]]; then
                    echo "DEBUG: fw_update() Hard timeout limit is reached, breaking the loop" >> $logfile
                    _sftp_timedout=true
                    break
                else
                    echo "DEBUG: fw_update() Waiting till hard timeout is reached.." >> $logfile
                fi
            else
                echo "ERROR: The update didn't complete within the time limit, timing out..." | tee -a $logfile
                _sftp_timedout=true
                break
            fi
        fi
        if ping -c1 -W2 $host > /dev/null; then
            # controller is reachable, check the update progress
            _ctrl_reachable=true
            echo "Getting the progress on fw update, please wait..." | tee -a $logfile
            # Prepare the batchfile (progress.bf) as an input for sftp.
            # The 'get progress' command returns the progress file (xml)
            # in pwd, so cd to the tmpdir to fetch the file there.
            printf '%s\n' "lcd $tmpdir" "get progress" > $tmpdir/progress.bf
            echo "DEBUG: contents of $tmpdir/progress.bf:" >> $logfile
            cat $tmpdir/progress.bf >> $logfile
            sftp_cmd_run "${tmpdir}/progress.bf"
            ctrl_activity_get "$tmpdir/progress"
            if [[ $ctrl_activity_a == "none" && $ctrl_activity_b == "none" ]]; then
                # no activity on any of the controller, update is finished
                # get the codeload status and parse it
                echo "DEBUG: fw_update() No ongoing activity on both controllers reported" >> $logfile
                if [[ $_ntry -gt 10 ]]; then
                    # no activity within first 20 mins could be a false alarm, check the
                    # codeload status only after 10 retries (~20 mins) are over
                    echo "No activity for more than 10 minutes, checking the codeload status" | tee -a $logfile
                    fw_codeload_status_get
                    echo "Parsing the codeload status" | tee -a $logfile
                    fw_update_status_parse
                    break
                fi
            elif [[ -z $ctrl_activity_a && -z $ctrl_activity_b ]]; then
                echo "DEBUG: fw_update() Could not get the progress from controller, update must be in progress, ignoring.." >> $logfile
            else
                echo "DEBUG: fw_update() Controllers has following activities:" >> $logfile
                echo "DEBUG: fw_update() ctrl_activity_a: $ctrl_activity_a" >> $logfile
                echo "DEBUG: fw_update() ctrl_activity_b: $ctrl_activity_b" >> $logfile
            fi
        else
            echo "DEBUG: fw_update() Controller host [$host] isn't reachable.." >> $logfile
            _ctrl_reachable=false
        fi
        # update in progress
        echo "Update is in progress, please wait, check the $logfile for more details..." | tee -a $logfile
        sleep $_sleep_time
        _ntry=$(( _ntry + 1 ))
    done

    if [[ "$_sftp_timedout" == true ]]; then
        echo "The fw update was timed out, checking the current firmware versions..." | tee -a $logfile
        if [[ "$_ctrl_reachable" == false ]]; then
            echo "ERROR: controller is not reachable, please check the firmware version manually, exiting with error." | tee -a $logfile
            exit 1
        fi
        fw_versions_compare "$controller_A_ver" "$controller_B_ver"
        case ${ret_fw_versions_compare} in
           0)
                # Update was successfull
                echo "SUCCESS!!! The fw versions on the controller are updated successfully " | tee -a $logfile
                echo "The detailed logs are captured at $logfile" | tee -a $logfile
                exit 0
            ;;
           1)
                # partial update, controller A is updated but controller B
                # is still on the older/original fw version.
                #TODO: find the way to check if controller B is still getting updated.
                echo "ERROR: The fw is updated on controller A but not on controller B" | tee -a $logfile
                echo "ERROR: Exiting on timeout, please check the status manually" | tee -a $logfile
                echo "ERROR: Please check $logfile for more details" | tee -a $logfile
                exit 1
            ;;
           2)
                # partial update, controller B is updated but controller A
                # is still on the older/original fw version.
                #TODO: find the way to check if controller A is still getting updated. 
                echo "ERROR: The fw is updated on controller B but not on controller A" | tee -a $logfile
                echo "ERROR: Exiting on timeout, please check the status manually" | tee -a $logfile
                echo "ERROR: Please check $logfile for more details" | tee -a $logfile
                exit 1
            ;;
           3)
                # Update was not successfull
                echo "ERROR: The controller fw update failed." | tee -a $logfile
                echo "ERROR: Please check $logfile for more details." | tee -a $logfile
                exit 1
            ;;
        esac
    fi

    if [[ $fw_update_status -eq 0 ]]; then
        echo "SUCCESS!! The firmware is updated successfully" | tee -a $logfile
        echo "The detailed logs are captured and kept at: '$logfile'" | tee -a $logfile
        exit 0
    else
        echo "Error: The controller firmware could not be updated" | tee -a $logfile
        echo "ERROR: Please check $logfile for more details, exiting with error $fw_update_status" | tee -a $logfile
        exit $fw_update_status
    fi
}

fw_license_show()
{
    fw_ver_get
    midplane_serial_get
    sc_license_get
}

ctrl_shutdown()
{
    echo "ctrl_shutdown(): Entry" >> $logfile
    if [[ "$shutdown_ctrl_name" = "A" || "$shutdown_ctrl_name" = "B" ]]; then
        shutdown_ctrl_name=$(echo $shutdown_ctrl_name | tr '[:upper:]' '[:lower:]')
    fi
    _cmd="shutdown $shutdown_ctrl_name"
    echo "ctrl_shutdown(): running command '$_cmd'" >> $logfile
    echo "Shutting down the storage controller: '$shutdown_ctrl_name'"
    if [[ $shutdown_ctrl_name = "a" || "$shutdown_ctrl_name" = "b" ]]; then
        cmd_run "$_cmd"
        _cmd="show controllers"
        _xml_obj_bt="controllers"
        _xml_obj_plist="status"
        _tmp_file="$tmpdir/show_controllers"
        _timeout=30
        _try=1
        _shutdown_status=false

        until $_shutdown_status != true
        do
            if [[ "$_try" -gt "$_timeout" ]]; then
                echo -ne " timeout!"  | tee -a $logfile
                echo -e "\nController did not shut down within stipulated timeout"  | tee -a $logfile
                echo "Please check the status manually" | tee -a $logfile
                exit 0
            fi
            cmd_run "$_cmd"
            parse_xml $xml_doc $_xml_obj_bt "${_xml_obj_plist[@]}" > $_tmp_file
            [ -s $_tmp_file ] || {
                echo "ctrl_shutdown(): No output from xmllint found" >> $logfile
                rm -rf $_tmp_file
                return 1
            }
            ret=$(grep -qE "OperationalDown|DownOperational" $_tmp_file)
            if [[ $ret -eq 0 ]]; then
                echo "Controller $shutdown_ctrl_name shutdown successfully"
                _shutdown_status=true
            fi
            echo -ne "."
            _try=$(( $_try + 1 ))
            sleep 4
        done
    elif [[ $shutdown_ctrl_name = "both" ]]; then
        # cmd_run "$_cmd" || {
        # try=1
        # _timeout=30
        # echo "waiting for controller to shutdown" 2>&1 | tee -a $logfile
        # until ! ping -c 1 $host 2>&1 > /dev/null
        # do
        #     if [[ "$try" -gt "$_timeout" ]]; then
        #         echo -ne " timeout!"
        #         echo -e "\nControllers did not shut down after $_timeout seconds"
        #         echo "Please check the status manually"
        #         exit 1
        #     fi
        #     echo -ne "."
        #     try=$(( $try + 1 ))
        #     sleep 4
        # done
        echo -ne " done!"
        echo -e "\nController is shutdown successfully" 2>&1 | tee -a $logfile
        exit 0
    fi
}

ctrl_restart()
{
    echo "ctrl_restart(): Entry" >> $logfile
    if [[ "$restart_ctrl_name" = "A" || "$restart_ctrl_name" = "B" ]]; then
        restart_ctrl_name=$(echo $restart_ctrl_name | tr '[:upper:]' '[:lower:]')
    fi
    _cmd="restart sc $restart_ctrl_name"
    echo "ctrl_restart(): running command '$_cmd'" >> $logfile
    echo "Restarting controller: '$restart_ctrl_name'"
    cmd_run "$_cmd" > $xml_doc || {
        try=1
        _timeout=30
        echo "waiting for controller to come up" 2>&1 | tee -a $logfile
        until ping -c 1 $host 2>&1 > /dev/null
        do
            if [[ "$try" -gt "$_timeout" ]]; then
                echo -ne " timeout!"
                echo -e "\nController did not come up after $_timeout seconds"
                echo "Please check the status manually"
                exit 1
            fi
            echo -ne "."
            try=$(( $try + 1 ))
            sleep 4
        done
        echo -ne " done!"
        echo -e "\nController restarted successfully" 2>&1 | tee -a $logfile
        exit 0
    }
}

disks_list()
{
    _dskinfo=$tmpdir/dskinfo
    echo "Getting disks details.. this might take time"
    disks_show_all > $_dskinfo
    [ -s $_dskinfo ] && cat $_dskinfo || {
        echo "Error: No disks found on the controller."
        exit 1
    }
}

do_provision()
{
    _prvinfo=$tmpdir/prvinfo

    [ "$pool_type" = "virtual" ] && license_check
    [ "$cleanup" = true ] && cleanup_provisioning
    [ "$default_prv" = true ] && {
        echo "main(): default provisioning" >> $logfile
        is_system_clean
        ret=$?
        [ $ret -eq 1 ] && {
            echo "Error: Controller is not in clean state"
            exit 1
        }
        disks_range_get
        [ -z "$range1" -o -z "$range2" ] && {
            echo "Error: Could not derive the disk list to create a pool"
            echo "Exiting."
            exit 1
        }
        # Provision the controller with provided input
        provision "$dflt_ptype" "$dflt_plvl" "$nvols" "$range1" "$dflt_p1nam"
        provision "$dflt_ptype" "$dflt_plvl" "$nvols" "$range2" "$dflt_p2nam"

        # Check if provisioning done successfully
        provisioning_info_get > $_prvinfo
        [ -s $_prvinfo ] && {
            echo "Controller provisioned successfully with following details:"
            cat $_prvinfo
         } || echo "Error: Controller could not be provisioned"
    }
    [ "$prvsnr_mode" = "manual" ] && {
        echo "main(): manual provisioning" >> $logfile

        # Provision the controller with provided input
        provision "$pool_type" "$pool_level" "$nvols" "$disk_range" "$pool_name"

        # Check if provisioning done successfully
        provisioning_info_get > $_prvinfo
        [ -s $_prvinfo ] && {
            echo "Controller provisioned successfully with following details:"
            cat $_prvinfo
         } || echo "Error: Controller could not be provisioned"
    }
    [ "$show_prov" = true ] && {
        provisioning_info_get > $_prvinfo
        [ -s $_prvinfo ] && cat $_prvinfo ||
            echo "No provisioning details found on the controller"
    }
}
