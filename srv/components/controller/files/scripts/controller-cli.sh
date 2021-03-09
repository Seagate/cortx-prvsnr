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

#set -euE

script_dir=$(dirname $0)
export logdir="/var/log/seagate/provisioner"
[ ! -d $logdir ] && mkdir -p $logdir

export tmpdir="$logdir/_ctrl_cli_tmp"
[ ! -d $tmpdir ] && mkdir -p $tmpdir

export logfile=$logdir/controller-cli.log

function trap_handler {
    echo "***** FAILED!! *****" | tee -a $logfile
    echo "For more details see $logfile" | tee -a $logfile
    echo "Exiting from trap_handler" >> $logfile
    exit 2
}

function trap_handler_exit {
    ret=$?
    if [[ $ret -ne 0 ]]; then
        echo "***** FAILED!! *****" | tee -a $logfile
        echo "For more details see $logfile" | tee -a $logfile
        echo "Exiting with return code: $ret" >> $logfile
    else
        echo "Exiting with return code: $ret" >> $logfile
    fi
    exit $ret
}

trap trap_handler ERR
trap trap_handler_exit EXIT

source $script_dir/provision.sh
source $script_dir/xml.sh

export cli_cmd
export element
export ret_txt
export vsize=0
export pool_type
export pool_level
export pool_name
export disk_range
export nvols=8
export default_prv=false
export cleanup=false
export show_prov=false
export show_license=false
export load_license=false
export restart_ctrl_opt=false
export shutdown_ctrl_opt=false
export restart_ctrl_name=""
export shutdown_ctrl_name=""
export license_file=""
export user=""
export pass=""
export host=""
export bc_tool="/usr/bin/bc"
export ssh_tool="/usr/bin/sshpass"
export ssh_base_cmd="/bin/ssh"
export ssh_opts="-o UserKnownHostsFile=/dev/null\
    -o StrictHostKeyChecking=no -o LogLevel=error"
export ssh_cred=""
export ssh_cmd=""
export remote_cmd=""
export range1
export range2
export dflt_ptype="linear"
export dflt_plvl="adapt"
export dflt_p1nam="dg01"
export dflt_p2nam="dg02"
export prvsnr_mode=""
export show_disks=false
export update_fw=false
export fw_bundle=""
export show_fw_ver=false
export show_license=false
export load_license=false
export ntp_opt=false
export ntp_server=""
export ntp_tz=""

usage()
{
  cat <<USAGE
  Utility to configure the Seagate Gallium stroage controller
  =========================================================
  usage:
  $0
         { host -h <hostname|ip> -u <username> -p <password> }
         [{ prov [-a|--all][-c|--cleanup][-s|--show-prov]
          [-t <pool-type> -l <level> -m <pool-name> -d <disk-range>]
          [-n <no-of-vols>] }]
         [-s|--show-disks]
         [-u|--update-fw]
         [--restart-ctrl <a|b>]
         [--shutdown-ctrl <a|b>]
         [-v|--show-fw-ver]
         [--show-license]
         [-l|--load-license]
         [-n|--ntp <ntp server ip/fqdn> "<timezone>"]
         [-h|--help]
USAGE
}

help()
{
    usage
    cat <<USAGE
    where:
    hostname      :- hostname or ip of the controller
    username      :- username of the controller to be provisioned,
                     user must have the manage role assigned to it
    password      :- password for the <username>
    pool-type     :- type of pool to be created - linear/virtual
    level         :- pool configuration level .e.g. adapt etc
                     supported levels: adapt
    pool-name     :- name of the pool to be created
                     for the virtual pool type the pool-name can only be either
                     'a' or 'b'
    disk-range    :- range of disks e.g. '0.0-9', '0.42-83', '0.0-5,0.7-20,0.24'
    no-of-vols    :- no of volumes to be created under the pool <pool-name>, the
                     argument is optional, by default 8 volumes in a pool will
                     be created
    -a|--all      :- Provisions the controller with standard configuration:
                     2 linear pools with 8 volumes per pool mapped to all
                     the initiators.
                     NOTE:- -a option is mutually exclusive to -t, -l, -m, -d
                     and the -n options.
    -c|--cleanup  :- Cleanups the existing provisioning (delete all pools)
    -s|--show-prov:- Shows current provisioning on the enclosure
    -u|--update-fw:- flash the provided firmware on the provided controller
    -v|--show-fw-ver:- Shows the firmware version
    --show-license:- Display license details along with storage enclosure
                     serial number and firmware version
    -s|--show-disks:- List the available disks (with relevant details) on the
                      controller.
    --restart-ctrl:- Restarts the specified controller (a|b), if second option
                     is blank both controllers will be restarted
    --shutdown-ctrl:- Shutdown the controller (a|b), if second option is ommited
                      then both the controllers will be shutdown
    -l|--load-license:-
    -n||--ntp        :- configure ntp (user provided server/ip & timezone) on controllers

    Sample commands:
    =========================================================

    1. To cleanup existing pools and provision with the default
       configuration for controller sati10b with following
       credentials(user/password) - admin/!admin

       $0 host -h 'sati10b' -u admin -p '!admin' prov -a -c

    2. Create an adapt linear pool dg01 with disks ranging from 0.0
       to 0.41 for controller with ip 192.168.1.1 and with following
       credentials(user/password) - admin/!paswd

       $0 host -h '192.168.1.1' -u admin -p '!paswd' prov -t linear -l adapt -m dg01 -d '0.0-41'

        Note: by default 8 volumes of equal size will also be created
        under the dg01 & and mapped to all the initiators. To override
        this behavior use -n arg under prov option to provide the no of
        volumes to be created, e.g. shown below.

    3. Provision a raid6 virtual pool named 'a' for disks range '0.42-0.83'
       & create 5 volumes under it. With controller host details as:
       host: host.seagate.com, user: admin, passwd: !passwd

       $0 host -h hostname -u admin -p '!passwd' prov -t virtual -l r6 -m a -d '0.42-0.83' -n 5

    4. Show the current provisioning on the controller host as:
       host10.seagate.com, admin, !passwd

       $0 host -h 'host.seagate.com' -u admin -p '!passwd' prov -s

    5. Show/List the disks on the controller host as:
       host10.seagate.com, admin, !passwd

       $0 host -h 'host.seagate.com' -u admin -p '!passwd' -s

    6. Restart the controller a:
       host10.seagate.com, admin, !passwd

       $0 host -h 'host.seagate.com' -u admin -p '!passwd' --restart-ctrl a

    7. Restart both the controller:
       host10.seagate.com, admin, !passwd

       $0 host -h 'host.seagate.com' -u admin -p '!passwd' --restart-ctrl

    8. Shutdown the controller a:
       host10.seagate.com, admin, !passwd

       $0 host -h 'host.seagate.com' -u admin -p '!passwd' --shutdown-ctrl a

    9. Shutdown both the controller:
       host10.seagate.com, admin, !passwd

       $0 host -h 'host.seagate.com' -u admin -p '!passwd' --shutdown-ctrl

    10. Configure NTP with ntp.seagate.com as a NTP server and +5:30 as timezone:
       $0 host -h 'host.seagate.com' -u admin -p '!passwd' -n ntp.seagate.com "+5:30"

USAGE
}

parse_hopts()
{
  unset $host
  unset $user
  unset $pass
  echo "parse_hopts(): nargs:$#, \$@=$@">> $logfile
  [ $# -lt 6 ] && echo "invalid input" && exit 1
  while getopts ':h:u:p:' opt 
  do
      case $opt in
        h) host="$OPTARG";;
        u) user="$OPTARG";;
        p) pass="$OPTARG";;
        ?) echo "Unrecognized option '$OPTARG' for host"; usage; exit 1;;
        *) usage; exit 1;;
      esac
  done
  [ -z "$pass" -o -z "$host" -o -z "$user" ] && {
        echo "Error: proper input not provided for host"
        usage
        exit 1
  }
  echo "parse_hopts():$host, $user" >> $logfile
  ssh_cred="$ssh_tool -p $pass"
  ssh_cmd="$ssh_base_cmd $ssh_opts $user@$host"
  remote_cmd="$ssh_cred $ssh_cmd"
}

parse_args()
{
    echo "parse_args(): parsing input arguments" >> $logfile
    host_optparse_done=false
    prov_optparse_done=false
    prvsnr_mode=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            host)
                if $host_optparse_done; then
                    echo "Error: host options already parsed"; exit 1
                fi
                echo "parse_args nargs=$#, args=$@" >> $logfile
                [ $# -lt 7 ] && {
                    echo "Error: insufficient arguments for host" && exit 1
                }
                hopts=("$2" "$3" "$4" "$5" "$6" "$7")
                parse_hopts "${hopts[@]}"
                shift 7
                host_optparse_done=true
                ;;
            prov)
                if $prov_optparse_done; then
                    echo "Error: prov options already parsed"; exit 1
                fi
                shift # this is to get rid of 'prov' 
                nvol_opt=false
                while [[ $# -gt 0 ]]
                do
                    case "$1" in
                        -a|--all)
                            default_prv=true
                            echo "parse_args(): default_prv=true">>$logfile
                            shift;;
                        -c|--cleanup)
                            cleanup=true;
                            echo "parse_args():clenaup=true" >>$logfile;shift;;
                        -s|--show-prov)
                            show_prov=true;
                            echo "parse_args():show_prov=true" >> $logfile
                            shift ;;
                        -t)
                            [ -z "$2" ] &&
                                echo "Error: pool-type not provided" && exit 1;
                            pool_type="$2"; shift 2;;
                        -l)
                            [ -z "$2" ] &&
                                echo "Error: pool-level not provided" && exit 1;
                            pool_level="$2"; shift 2 ;;
                        -m)
                            [ -z "$2" ] &&
                                echo "Error: pool-name not provided" && exit 1;
                            pool_name="$2"; shift 2 ;;
                        -d)
                            [ -z "$2" ] &&
                                echo "Error: disk-range not provided" && exit 1;
                            disk_range="$2"; shift 2 ;;
                        -n)
                            [ -z "$2" ] &&
                                echo "Error: nvols not provided" && exit 1;
                            nvols="$2"; nvol_opt=true;shift 2 ;;
                        *) break ;;
                    esac
                done
                [ ! -z "$pool_type" -a ! -z "$pool_level" -a \
                    ! -z "$pool_name" -a ! -z "$disk_range" ] && {
                        echo "parse_args(): manual provisioning" >> $logfile
                        prvsnr_mode="manual"
                } || {
                    [ ! -z "$pool_type" -o ! -z "$pool_level" -o\
                        ! -z "$pool_name" -o ! -z "$disk_range" ] && {
                            echo "parse_args():partial opts provided" >>$logfile
                            prvsnr_mode="partial"
                            echo "Error: Incomplete arguments provided"\
                                "for prov, make sure all of the [t|l|m|d]"\
                                "options are provided, exiting..." 
                            echo "Error, exiting.."
                        exit 1
                    }
                }
                echo "parse_args(): default_prv=$default_prv" >> $logfile
                echo "parse_args(): prvsnr_mode='$prvsnr_opts'" >> $logfile
                [ "$default_prv" = true -a ! -z "$prvsnr_mode" ] && {
                    echo "Error: the prov options [-a|--all] and"\
                        "-[t|l|m|d|n] are mutually exclusive,"\
                        " please use either of them, exiting.." 
                        exit 1
                }
                [ "$prvsnr_mode" = "manual" ] && {
                    [ $pool_type != "linear" -a $pool_type != "virtual" ] && {
                        echo "Error: Invalid pool-type provided,"\
                            "only 'linear' or 'virtual' are supported, exiting.."
                        exit 1
                    }
                    [ $pool_type = "virtual" ] && {
                        [ $pool_name != "a" -a $pool_name != "b" ] && {
                            echo "Error: Invalid 'virtual' pool-name provided"\
                                "'virtual' pool-type can only be 'a' or 'b'"
                            echo "Error, exiting"
                            exit 1
                        }
                    }
                }
                # exit if none of the prov option is provided
                [ "$default_prv" = false -a "$prvsnr_mode" != "manual" -a\
                    "$cleanup" = false -a "$show_prov" = false ] && {
                        echo "Error: Insufficient prov opts provided"
                        exit 1
                }
                prov_optparse_done=true
                echo "parse_args(): continue: opt: $#, $@">> $logfile
                continue
                ;;
            -h|--help) help; exit 0 ;;
            -s|--show-disks)
                echo "parse_args(): show disks" >> $logfile
                if $prov_optparse_done; then
                    echo "Error: prov options already parsed"; exit 1
                fi
                show_disks=true
                shift
                ;;
            -u|--update-fw)
                echo "parse_args(): update firmware" >> $logfile
                update_fw=true
                [ -z "$2" ] &&
                    echo "Error: firmware bundle not provided" && exit 1;
                fw_bundle="$2"; shift 2
                [ "$prov_optparse_done" = true ] &&
                    echo "Error: firmware and prov options are not supported"\
                        "together.." && exit 1
                ftp_op=true ;;
            -v|--show-fw-ver)
                echo "parse_args(): update firmware" >> $logfile
                show_fw_ver=true
                [ "$prov_optparse_done" = true ] &&
                    echo "Error: firmware and prov options are not supported"\
                        "together.." && exit 1
                shift
                ;;
            --show-license)
                echo "parse_args(): show license" >> $logfile
                show_license=true
                shift
                ;;
            -l|--load-license)
                echo "parse_args(): load license" >> $logfile
                [ "$prov_optparse_done" = true ] &&
                    echo "Error: firmware and prov options are not supported"\
                        "together.." && exit 1
                load_license=true
                [ -z "$2" ] &&
                    echo "Error: License file not provided" && exit 1;
                license_file="$2"
                shift 2 ;;
            --restart-ctrl)
                echo "parse_args(): restart ctrl" >> $logfile
                [ "$prov_optparse_done" = true ] &&
                    echo "Error: firmware and prov options are not supported"\
                        "together.." && exit 1
                [ "$shutdown_ctrl_opt" = true ] &&
                    echo "Error: Restart and shutdown options are not supported"\
                        "together.." && exit 1
                restart_ctrl_opt=true
                [ -z "$2" ] && {
                    restart_ctrl_name="both";
                    shift;
                } || {
                    if [[ "$2" != 'a' && "$2" != 'A' ]] &&
                       [[ "$2" != 'b' && "$2" != 'B' ]]; then
                        echo "Error: Invalid controller name provided"
                        exit 1
                    fi
                    restart_ctrl_name="$2"
                    shift 2
                 }
                ;;
            --shutdown-ctrl)
                echo "parse_args(): shutdown ctrl" >> $logfile
                [ "$prov_optparse_done" = true ] &&
                    echo "Error: firmware and prov options are not supported"\
                        "together.." && exit 1
                [ "$restart_ctrl_opt" = true ] &&
                    echo "Error: Restart and shutdown options are not supported"\
                        "together.." && exit 1
                shutdown_ctrl_opt=true
                [ -z "$2" ] && {
                    shutdown_ctrl_name="both";
                    shift;
                } || {
                    if [[ "$2" != 'a' && "$2" != 'A' ]] &&
                       [[ "$2" != 'b' && "$2" != 'B' ]]; then
                        echo "Error: Invalid controller name provided"
                        exit 1
                    fi
                    shutdown_ctrl_name="$2"
                    shift 2
                 }
                ;;
            -n|--ntp)
                echo "parse_args(): configure ntp" >> $logfile
                if [[ -z "$2" ]]; then
                    echo "Error: NTP server not provided" && exit 1;
                fi
                if [[ -z "$3" ]]; then
                    echo "Error: Timezone not provided" && exit 1;
                fi
                ntp_server="$2"
                _tz=":${3}"
                ntp_tz=$(TZ="$_tz" date +%:z)
                echo "parse_args(): ntp_server=$ntp_server, _tz=${_tz}, ntp_tz=$ntp_tz" >> $logfile
                shift 3
                ntp_opt=true ;;
            *) echo "Invalid option $1"; exit 1;;
        esac
    done
    [ "$host_optparse_done" = false ] &&
        echo "Error: Controller details not provided, exiting.." | tee -a $logfile && exit 1

    [ "$prov_optparse_done" = false -a "$show_disks" = false -a\
        "$show_license" = false -a "$load_license" = false -a\
        "$show_fw_ver" = false -a "$update_fw" = false -a\
        "$shutdown_ctrl_opt" = false -a "$restart_ctrl_opt" = false -a\
        "$ntp_opt" = false ] && {
        echo "Error: Incomplete arguments provided, exiting.." | tee -a $logfile
        exit 1
    }
    echo "parse_args(): parsing done" >> $logfile
    return 0
}

input_params_validate()
{
    _test_cmd="show version"
    $remote_cmd $_test_cmd > /tmp/version.xml
    ret=$?
    case $ret in
        0)
            echo "Info: The host details [host: $host user: $user] & the password provided are correct" >> $logfile
            ;;
        5)  echo "Error: The credentials [user: $user & password] provided are not correct" | tee -a $logfile 
            echo "Error: Please provide the correct credentials and try again" | tee -a $logfile
            exit 1
            ;;
        255)
            echo "Error: The hostname [host: $host ] provided is not reachable" | tee -a $logfile 
            echo "Error: Please provide the correct host details and try again" | tee -a $logfile
            exit 1
            ;;
        *)
            echo "Error: ssh command failed with error $ret while connecting to host [host: $host]" | tee -a $logfile 
            echo "Error: Please ensure the host is reachable over ssh and try again" | tee -a $logfile
            exit 1
        ;;
    esac
}

main()
{
    echo -e "\n-------------- Running $0 -----------------" >> $logfile
    timestamp=$(date)
    echo "Runtime: $timestamp" >> $logfile
    echo "Inpupt arguments provided: $@" >> $logfile
    parse_args "$@"
    reqd_pkgs_install "$ssh_tool" "$xml_cmd" "$bc_tool"

    # Decrypt the password. Required only for commands received from api
    if [[ "$update_fw" = true || "$restart_ctrl_opt" = true
        || "$shutdown_ctrl_opt" = true || "$ntp_opt" = true ]]; then
        echo "main(): Decrypting the password received from api" >> $logfile
        pass=`salt-call lyveutil.decrypt storage ${pass} --output=newline_values_only`
        #echo "main(): decrypted password: $pass" >> $logfile
        ssh_cred="$ssh_tool -p $pass"
        ssh_cmd="$ssh_base_cmd $ssh_opts $user@$host"
        remote_cmd="$ssh_cred $ssh_cmd"
    fi

    input_params_validate
    [ "$prov_optparse_done" = true ] && do_provision
    [ "$show_disks" = true ] && disks_list
    [ "$load_license" = true ] && fw_license_load
    [ "$update_fw" = true ] && fw_update
    [ "$show_fw_ver" = true ] && fw_ver_get
    [ "$show_license" = true ] && fw_license_show
    [ "$restart_ctrl_opt" = true ] && ctrl_restart
    [ "$shutdown_ctrl_opt" = true ] && ctrl_shutdown
    [ "$ntp_opt" = true ] && ntp_config

    rm -rf $tmpdir $xml_doc
    echo "***** SUCCESS! *****" 2>&1 | tee -a $logfile
    echo "The detailed logs are kept at: $logfile"
}

main "$@"
