#!/bin/bash
export logdir="/opt/seagate/eos-prvsnr/generated_configs/sc"
[ ! -d $logdir ] && mkdir -p $logdir

export fw_logfile="$logdir/controller-fw-update.log"
[ -f $fw_logfile ] && rm -rf $fw_logfile

script_dir="$PWD"
controller_script="$script_dir/controller-cli.sh"

usage()
{
    cat <<USAGE
    Usage:
    $0 -c1 <controller-A> -c2 <controller-B> -u <username> -p '<password>'\
     <firmware_bundle_file>
    Where,
        controller-A         :- hostname or ip address of controller-A
        controller-B         :- hostname or ip address of controller-B
        username             :- username of the controller to be provisioned,
                                user must have the manage role assigned to it
        password             :- password for given username
        firmware_bundle_file :- '.bundle' file for firmware update 
USAGE
}

parse_opts()
{
    unset $cntrl_a
    unset $cntrl_b
    unset $user
    unset $pass
    echo "parse_opts(): No. of arguments:$#, arguments=$@">> $fw_logfile
    [ $# -lt 8 ] && {
        echo "Insufficient arguments provided" && usage && exit 1
    }
    while getopts 'c1:c2:u:p:' opt 
    do
        case $opt in
            c1) cntrl_a="$OPTARG";;
            c2) cntrl_b="$OPTARG";;
            u) user="$OPTARG";;
            p) pass="$OPTARG";;
            ?) echo "Unrecognized option '$OPTARG'"; usage; exit 1;;
            *) usage; exit 1;;
        esac
    done
    [ -z "$cntrl_a" -o -z "$cntrl_b" -o -z "$user" -o -z "$pass" ] && {
        echo "Error: proper input not provided" && usage && exit 1
    }    
}

parse_args()
{
    [ $# -lt 9 ] && {
        echo "Error: Insufficient arguments provided" && usage && exit 1
    }
    parse_opts $1 $2 $3 $4 $5 $6 $7 $8
    fw_bundle=$9
    [ -z "$fw_bundle" ] && {
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
    update_fw $cntrl_a $cntrl_b $user $pass $fw_bundle
}  

main "$@"