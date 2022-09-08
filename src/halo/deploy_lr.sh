#!/bin/bash

# Log Levels:
DEBUG=1
INFO=2
WARNING=3
ERROR=4
FATAL=5
DEFAULT_LOG_LEVEL=${DEFAULT_LOG_LEVEL:-$INFO}

function log {
    LEVEL=$1; shift
    LOG_LEVEL=${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}
    [[ $LEVEL -lt $LOG_LEVEL ]] && return

    echo "log: $*"
}

function show_usage {
    echo -e "usage: $(basename $0) [-f SOLUTION-CONFIG] [-c CONFIG-URL] [-l LOG-LEVEL]"
    echo -e "Where:"
    echo -e "..."
    echo -e " SOLUTION-CONFIG : Solution-Config directory containing -\
                                config.yaml, cluster.yaml and secrets.yaml"
    echo -e "                   (Default: /etc/solution)"
    echo -e " LOG-LEVEL       : Log Level (Default: 2)"
    echo -e "                   Supported log levels:"
    echo -e "                   DEBUG=1, INFO=2, WARNING=3, ERROR=4, FATAL=5"
    echo -e " CONFIG-URL: URL of storing Configuration"
    exit 1
}

function make_url {
    local config=$1
    echo "yaml://$config"
}

function conf_get {
    URL=$1; key=$2
    val=$(conf $URL get $key)
    val=$(echo $val | tr -d "["\" | tr -d "\"]")
    echo $val
}

SOLUTION_CONFIG="/etc/solution"

while [ $# -gt 0 ];  do
    case $1 in
    -l )
        shift 1
        LOG_LEVEL=$1
        ;;
    -f )
        shift 1
        SOLUTION_CONFIG=$1
        ;;
    -c )
        shift 1
        CONFIG_URL=$1
        ;;
    -h )
        show_usage
        ;;
    * )
        echo -e "Invalid argument provided : $1"
        show_usage
        exit 1
        ;;
    esac
    shift 1
done

# setup ansible cluster
for file in "$SOLUTION_CONFIG"/*
do
    [[ ! -f "$file" ]] && return
    if [[ "$(conf_get $(make_url $file) 'cluster')" != "null" ]]
    then
        log $INFO "/opt/seagate/halo/ansible/ansible_setup config -f $(make_url $file)"
        /opt/seagate/halo/ansible/ansible_setup config -f $(make_url $file)
    fi
done

# Execute Provisioner Entrypoint script
ansible -m shell -a "/opt/seagate/cortx/provisioner/bin/cortx_deploy -f "$SOLUTION_CONFIG" -c "$CONFIG_URL"" all

