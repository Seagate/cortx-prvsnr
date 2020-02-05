#!/bin/bash
export logdir="/opt/seagate/eos-prvsnr/generated_configs/sc"
[ ! -d $logdir ] && mkdir -p $logdir

export fw_logfile=$logdir/controller-fw-update.log
[ -f $fw_logfile ] && rm -rf $fw_logfile

controller_script="/opt/seagate/eos-prvsnr/srv/components/controller/files/scripts/controller-cli.sh"

usage()
{
    cat <<USAGE
    Usage:
    $0 <controller-1> <controller-2> -u <username> -p '<password>'\
     <firmware_bundle_file>
    Where,
        controller-1         :- hostname or ip address of controller-1
        controller-2         :- hostname or ip address of controller-1
        username             :- username of the controller to be provisioned,
                                user must have the manage role assigned to it
        password             :- password for given username
        firmware_bundle_file :- '.bundle' file for firmware update 
USAGE
}

parse_opts()
{
    unset $user
    unset $pass
    echo "parse_opts(): No. of arguments:$#, arguments=$@">> $fw_logfile
    [ $# -lt 4 ] && {
        echo "Insufficient arguments provided" && usage && exit 1
    }
    while getopts 'u:p:' opt 
    do
        case $opt in
            u) user="$OPTARG";;
            p) pass="$OPTARG";;
            ?) echo "Unrecognized option '$OPTARG'"; usage; exit 1;;
            *) usage; exit 1;;
        esac
    done
    [ -z "$user" -o -z "$pass" ] && {
        echo "Error: proper input not provided" && usage && exit 1
    }    
}

parse_args()
{
    [ $# -lt 7 ] && {
        echo "Error: Insufficient arguments provided" && usage && exit 1
    }
    cntrl_1=$1
    cntrl_2=$2
    parse_opts $3 $4 $5 $6
    fw_bundle=$7
    [ -z "$cntrl_1" -o -z "$cntrl_2" -o -z "$fw_bundle" ] && {
        echo "Error: proper input not provided" && usage && exit 1
    }
}

update_fw()
{
    echo "update_fw(): no. of arguments-$#, arguments-$@" >> $fw_logfile
    [ $# -lt 5 ] && {
        echo "Insufficient arguments provided" && exit 1
    }
    declare -a _controllers=($1 $2)
    _user=$3
    _pass=$4
    _fw_bundle=$5
    for _controller in ${_controllers[@]}; do
        $controller_script host -h $_controller -u $_user -p $_pass --update-fw $_fw_bundle
        [ $? -eq 1 ] && {
            echo "Error: Command execution failed"
        }
    done
}

main()
{
    parse_args "$@"
    update_fw $cntrl_1 $cntrl_2 $user $pass $fw_bundle
}  

main "$@"