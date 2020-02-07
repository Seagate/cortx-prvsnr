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
    -F <firmware_bundle>
    Where,
        controller-A         :- hostname or ip address of controller-A
        controller-B         :- hostname or ip address of controller-B
        username             :- username of the controller to be provisioned,
                                user must have the manage role assigned to it
        password             :- password for given username
        firmware_bundle      :- target firmware bundle to update the controller 
USAGE
}

parse_args()
{
    [ $# -lt 10 ] && {
        echo "Error: Insufficient arguments provided" && usage && exit 1
    }
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c1)
               controller_A=$2; shift 2 ;;
            -c2)
               controller_B=$2; shift 2 ;;
            -u)
               user=$2; shift 2 ;;
            -p)
               pass=$2; shift 2 ;;
            -F)
               fw_bundle=$2; shift 2 ;;
            *) echo "Error: Invalid option $1"; exit 1;;      
         esac
    done
    [ -z "$controller_A" -o -z "$controller_B" -o -z "$user" -o -z "$pass" -o -z "$fw_bundle" ] && {
        echo "Error: proper input not provided" && usage && exit 1
    }
}

update_fw()
{
    echo "update_fw(): no. of arguments-$#, arguments-$@" >> $fw_logfile
    [ $# -lt 5 ] && {
        echo "Error: Insufficient arguments provided" && exit 1
    }
    declare -a _controllers=($1 $2)
    _user=$3
    _pass=$4
    _fw_bundle=$5
    for _controller in "${_controllers[@]}"; do
        $controller_script host -h $_controller -u $_user -p $_pass --update-fw $_fw_bundle
        [ $? -eq 1 ] && {
            echo "Error: Command execution failed"
        }
    done
}

main()
{
    parse_args "$@"
    update_fw $controller_A $controller_B $user $pass $fw_bundle
}  

main "$@"