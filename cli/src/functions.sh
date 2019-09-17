#!/bin/bash

# general set of arguments
cluster=false
dry_run=False
hostspec=
ssh_config=
sudo=
verbosity=0

function combine_usage_options {
    local _add_opts_info=${1:-''}
    local _base_opts_info="\
    -c,  --cluster                  treat host as cluster primary
    -n,  --dry-run                  do not actually perform any changes
    -h,  --help                     print this help and exit
    -r,  --remote [user@]hostname   remote host specification
    -F,  --ssh-config FILE          alternative path to ssh configuration file
    -s,  --sudo                     use sudo
    -v,  --verbose                  be more verbose
"
    echo "\
        
Options:
$_base_opts_info
$_add_opts_info
"
}


function usage {
  local _opts_info=$(combine_usage_options)
  echo "\
Usage: $0 [options]

$_opts_info
"
}


function parse_args {
    set -eu

    echo "$@"

    local _add_opts=$1
    local _add_long_opts=$2
    local _opts_cb=$3
    local _res
    shift 3

    # Note. this mostly based on https://stackoverflow.com/a/29754866

    ! getopt --test > /dev/null
    if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
        echo 'Error: getopt is not functional (`getopt --test` failed).'
        exit 1
    fi

    local _opts=cnhr:F:sv
    if [[ -n $_add_opts ]]; then
        _opts=$_opts$_add_opts
    fi

    local _long_opts=cluster,dry-run,help,remote:,ssh-config:,sudo,verbose
    if [[ -n $_add_long_opts ]]; then
        _long_opts=$_long_opts,$_add_long_opts
    fi

    ! PARSED=$(getopt --options=$_opts --longoptions=$_long_opts --name "$0" -- "$@")
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        exit 2
    fi

    eval set -- "$PARSED"

    while true; do
        case "$1" in
            -c|--cluster)
                cluster=true
                shift
                ;;
            -n|--dry-run)
                dry_run=True
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -r|--remote)
                hostspec="$2"
                shift 2
                ;;
            -F|--ssh-config)
                ssh_config="$2"
                if [[ ! -f "$ssh_config" ]]; then
                    >&2 echo "'$ssh_config' not a file"
                    exit 2
                fi
                shift 2
                ;;
            -s|--sudo)
                sudo=sudo
                shift
                ;;
            -v|--verbose)
                ((verbosity=verbosity+1))
                shift
                ;;
            --)
                shift
                break
                ;;
            *)
                if [[ "$1" == '?' ]]; then
                    >&2 echo "Programming error"
                    exit 3
                else
                    set +e
                    $_opts_cb "$@"
                    _res=$?
                    set -e
                    shift $_res
                fi
                ;;
        esac
    done

    if [[ $# -ne 0 ]]; then
        >&2 echo "$0: No positional arguments are expected, provided: $@"
        exit 4
    fi

    if [[ $verbosity -gt 0 ]]; then
        echo "Parsed args: 'cluster'=$cluster, 'dry-run'=$dry_run, 'remote'=$hostspec, 'ssh-config'=$ssh_config, 'sudo'=$sudo, 'verbosity'=$verbosity, 'positional'=$@"
    fi
}


function prepare_command() {
    local _sudo=${1:-$sudo}
    local _hostspec=${2:-$hostspec}
    local _ssh_config=${3:-$ssh_config}

    # prepare command
    local _cmd="$_sudo"
    if [[ -n "$_hostspec" ]]; then

        if [[ -n "$_ssh_config" ]]; then
            _ssh_config="-F $_ssh_config"
        fi

        if [[ -n "$_sudo" ]]; then
            _ssh_config="-t $_ssh_config"
        fi

        _cmd="ssh $_ssh_config $_hostspec $_cmd"
    fi

    echo "$_cmd"
}
