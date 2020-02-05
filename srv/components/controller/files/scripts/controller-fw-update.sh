#!/bin/bash
export logdir="/opt/seagate/eos-prvsnr/generated_configs/sc"
[ ! -d $logdir ] && mkdir -p $logdir

export fw_logfile=$logdir/controller-fw-update.log
[ -f $logfile ] && rm -rf $logfile

usage()
{
    cat <<USAGE
    $0 controller-1-ip controller-2-ip -u <username> -p '<password>' <firmware_bundle_file>  
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
}

parse_args()
{
    [ $# -lt 7 ] && {
        echo "Error: Insufficient arguments provided" && usage && exit 1
    }
    declare -a controllers=($1 $2)
    parse_opts $3 $4 $5 $6
    fw_bundle=$7
}

update_fw()
{
    echo "update_fw(): no. of arguments-$#, arguments-$@" >> $fw_logfile
    for controller in ${controllers[@]}; do
        source "$controller_script -h $controller -u $user -p "$pass" --update-fw $fw_bundle"
        [ $? -eq 1 ] && {
            echo "Error: Command execution failed"
        }
    done    
}

main()
{
    parse_args "$@"
    update_fw
}  

main "$@"