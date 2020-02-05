#!/bin/bash
export logdir="/opt/seagate/eos-prvsnr/generated_configs/sc"
[ ! -d $logdir ] && mkdir -p $logdir

export logfile=$logdir/controller.log
[ -f $logfile ] && rm -rf $logfile

usage()
{
    cat <<USAGE
    $0 controller-1-ip controller-2-ip -u <username> -p '<password>'   
USAGE
}

parse_opts()
{
    unset $user
    unset $pass
    echo "parse_opts(): No. of arguments:$#, arguments=$@">> $logfile
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
    [ $# -lt 6 ] && {
        echo "Error: Insufficient arguments provided" && usage && exit 1
    }
    cntrl_1=$1
    cntrl_2=$2
    shift 2
    parse_opts "$@"
}

main()
{
    parse_args "$@"
    echo "Arguments: $cntrl_1 $cntrl_2 $user $pass"
}  

main "$@"