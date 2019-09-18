#!/bin/bash

# general set of arguments
# TODO should be added to docs as part of the API
cluster=false
dry_run=false
hostspec=
ssh_config=
sudo=false
verbosity=0
positional_args=

base_options_usage="\
  -c,  --cluster                  treat host as cluster primary
  -n,  --dry-run                  do not actually perform any changes
  -h,  --help                     print this help and exit
  -r,  --remote [user@]hostname   remote host specification
  -F,  --ssh-config FILE          alternative path to ssh configuration file
  -s,  --sudo                     use sudo
  -v,  --verbose                  be more verbose
"

# default usage
# TODO mention in docs how to override
function usage {
  echo "\
Usage: $0 [options]

Options:
$base_options_usage
"
}


# API:
#   - parse_args <add_opts_short> <add_opts_long> <add_opts_parse_cb> <options_to_parse>
#   - add_opts_short a string of one-letter additional options
#   - add_opts_long  a comma-separated string of long additional options
#   - add_opts_parse_cb a function name to call to parse additional options
#       - should raise an error (e.g. exit) if something goes wrong
#   - parsed values for base set of options are assigned to global variables:
#       - cluster
#       - dry_run
#       - hostspec
#       - ssh_config
#       - sudo
#       - verbosity
#   - positional arguments are set to positional_args global variable
#   - exits in case of an error, exit codes:
#       - 0: success
#       - 1: getopt can't be used in the environment (self getopt's test fails)
#       - 2: command line arguments don't satisfy the specification
#           (e.g. unknown option or missed required argument)
#       - 3: some other getopt error
#       - 4: options parser callback is not defined when it is expected
#       - 5: bad argument values (e.g. not a file for ssh-config)


function parse_args {
    set -eu

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

    # TODO why eval here
    eval set -- "$PARSED"

    while true; do
        case "$1" in
            -c|--cluster)
                cluster=true
                shift
                ;;
            -n|--dry-run)
                dry_run=true
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
                    exit 5
                fi
                shift 2
                ;;
            -s|--sudo)
                sudo=true
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
                    if [[ -z "$_opts_cb" ]]; then
                        >&2 echo "Options parser callback is not defined"
                        exit 4
                    fi

                    $_opts_cb "$@"

                    local _opt=$(echo "$1" | sed 's/^-\+//g')
                    if (echo "$_add_opts" | grep -qP "$_opt(?=:)") || (echo ",$_add_long_opts" | grep -qP ",$_opt(?=:)"); then
                        shift 2
                    else
                        shift
                    fi
                fi
                ;;
        esac
    done

    positional_args="$@"
}


function build_command() {
    set -eu

    local _cmd=''
    if [[ -n "$hostspec" ]]; then
        _cmd='ssh'

        if $sudo; then
            _cmd="$_cmd -t"
        fi

        if [[ -n "$ssh_config" ]]; then
            _cmd="$_cmd -F $ssh_config"
        fi

        _cmd="$_cmd $hostspec"
    fi

    if $sudo; then
        _cmd="$_cmd sudo"
    fi

    echo $_cmd
}
