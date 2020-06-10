#!/bin/bash - 
##======================================================================
# This script is meant for quick & easy install via:
#   $ sh install.sh
#========================================================================      
#	title           	: setup.sh
#	description     	: This script will provision _manage_iq VM on given user account.
#	author		 		: RE
#	date            	: 20200210
#	version         	: 0.1   
#	usage		 		: bash setup.sh -h {hostname} -x {auth-token}
#	bash_version    	: 4.2.46(2)-release
#=========================================================================


# Mthod will perform REST operations 'GET', 'POST'
_do_rest(){

    REST_ENDPOINT=$1
    REST_CRED=$2
    REST_METHOD=$3
    REST_DATA=$4

    response=$(curl -s --insecure --user "${REST_CRED}" -H "Accept: application/json" --request "${REST_METHOD}" ${REST_DATA} "${REST_ENDPOINT}" )     
    echo ${response}
}


# Verify/install the required dependency before execution
_check_dependencies(){

    _console_log " [ _check_dependencies ] : Initiated......"

    declare -a dependency_tools=("jq" "nmap")

    for dt in "${dependency_tools[@]}"
    do
       if command -v ${dt} >/dev/null 2>&1 ; then
            _console_log " [ _check_dependencies ] : '${dt^^}' Already Installed "
        else
            _console_log " [ _check_dependencies ] : '${dt^^}' Not Found, Started installing '${dt^^}'....."

            if [ -f /etc/redhat-release ]; then
                yum install ${dt} -y
            elif [ -f /etc/lsb-release ]; then
                apt-get install ${dt} -y
            fi
        fi

    _console_log " [ _check_dependencies ] : '${dt^^}' Version Installed : $(${dt} --version | sed -r '/^\s*$/d' | head -n 1)"
    done
}

# Generic logging mechanisum
_console_log(){

    MESSAGE=$1
    TYPE=$2

    underline="----------------------------------------------------------------------------"
    
    if [ "$TYPE" == "0" ]; then
        printf "\n\n"
        echo $MESSAGE >&2
        echo ${underline:0:${#MESSAGE}} >&2
        printf "\n\n"
    elif [ "$TYPE" == "1" ]; then
        echo -ne $MESSAGE >&2
    else
        echo $MESSAGE >&2
    fi
}

#Generic Json Response quering using JQ
_get_response(){
    DATA=$1
    KEY=$2
    if [ -z "$DATA" ] || [ -z "$KEY" ];
    then
        _console_log "[ _get_response ] : API Response is Null  - '$ACTION'" 1
        exit 1
    else
        result=$(echo "${DATA}" | jq -r ".${KEY}" | tr -d '[ \n]')
        echo $result
    fi
}

# Manage IQ REST Request catelog
_manage_iq(){

    ACTION=$1

    #_console_log "[ _manage_iq ] : Action Initiated - '$ACTION'"
    
    case $ACTION in
        GET_VM)
            QUERY_DATA="-G --data-urlencode expand=resources --data-urlencode attributes=name,vendor,snapshots --data-urlencode filter[]=name=${VM_NAME}"
            response=$(_do_rest "${MIQ_VM_SEARCH_ENDPOINT}" "${MIQ_CRED}" "GET" "${QUERY_DATA}")
        ;;
        GET_VM_STATUS)
            response=$(_do_rest "${MIQ_VM_ENDPOINT}" "${MIQ_CRED}" "GET" "")
            response=$(_get_response "${response}" 'power_state')
        ;;
        START_VM) 
            POST_DATA="--data {\"action\":\"start\"}"
            response=$(_do_rest "${MIQ_VM_ENDPOINT}" "${MIQ_CRED}" "POST" "$POST_DATA")
            response=$(_get_response "${response}" 'message')
        ;;
        STOP_VM)
            POST_DATA="--data {\"action\":\"stop\"}"
            response=$(_do_rest "${MIQ_VM_ENDPOINT}" "${MIQ_CRED}" "POST" "$POST_DATA")
            response=$(_get_response "${response}" 'message')
        ;;
        REVERT_VM_SNAPSHOT)
            POST_DATA="--data {\"action\":\"revert\"}"
            response=$(_do_rest "${MIQ_VM_SNAPSHOT_ENDPOINT}" "${MIQ_CRED}" "POST" "$POST_DATA")
            response=$(_get_response "${response}" 'message')
        ;;
        GET_API)
            response=$(_do_rest "${MIQ_API_ENDPOINT}" "${MIQ_CRED}" "GET" "")
        ;;
    esac 

    echo ${response}
}

# Preload functinalities
_preload() {

    _console_log " [1] - Pre Checks Initiated for VM : $VM_NAME" 0

    MIQ_HOST="https://ssc-cloud.colo.seagate.com"
    MIQ_API_ENDPOINT="${MIQ_HOST}/api"
    MIQ_VM_SEARCH_ENDPOINT="${MIQ_HOST}/api/vms"

    
    _check_dependencies

    _validate_input_params

    response=$(_manage_iq 'GET_VM')
    MIQ_VM_ENDPOINT=$(echo $response | jq -r '.resources[0].href')
    MIQ_VM_SNAPSHOT_ENDPOINT="${MIQ_VM_ENDPOINT}/snapshots/$(echo $response | jq -r '.resources[0].snapshots |=sort_by(.created_on) | .resources[0].snapshots[0].id')"

    _console_log " [ _preload ] : VM_HOST - $VM_HOST"
    _console_log " [ _preload ] : MIQ_VM_ENDPOINT - $MIQ_VM_ENDPOINT"
    _console_log " [ _preload ] : MIQ_VM_SNAPSHOT_ENDPOINT - $MIQ_VM_SNAPSHOT_ENDPOINT"
}

# Logic to ensure VM state change
_wait_for_vm_state_change() {

    expected_vm_state=$1
    current_vm_state=$(_manage_iq 'GET_VM_STATUS')

    n=0
    _console_log " [ _wait_for_vm_state_change ] :" 1
    while [ "$n" -lt 50 ] && [ "$expected_vm_state" != "$current_vm_state" ]; do
        current_vm_state=$(_manage_iq 'GET_VM_STATUS')
        _console_log "=>" 1
        n=$(( n + 1 ))
        sleep 10
    done
    _console_log "Done"
}

# Change VM state based on input param
_change_vm_state(){

    change_vm_state=$1
    retry_on_fail=$2
    current_vm_state=$(_manage_iq 'GET_VM_STATUS')

    _console_log " [ _change_vm_state ] : Current VM State - '$current_vm_state' , Expected VM State Change - '$change_vm_state' "
    
    if [ "$current_vm_state" != "$change_vm_state" ];then

        if [ "$change_vm_state" == "on" ];then
            vm_change_state_response=$(_manage_iq 'START_VM')
        else
            vm_change_state_response=$(_manage_iq 'STOP_VM')
        fi
        _console_log " [ _change_vm_state ] : Change Request Message - $vm_change_state_response"
        
        _wait_for_vm_state_change "$change_vm_state"
        
        current_vm_state=$(_manage_iq 'GET_VM_STATUS')

        if [ "$change_vm_state" == "$current_vm_state" ];then
            _console_log "[ _change_vm_state ] : VM State changed to $current_vm_state successfully"
        else

            if [ "$retry_on_fail" == "1" ];then
               
                _console_log "[ _change_vm_state ] : Retry Initated current VM State - $current_vm_state"
                
                # TEMP FIX for VM Issue
                _manage_iq 'STOP_VM'
                _manage_iq 'START_VM'

                _change_vm_state "$change_vm_state"
            else
                _console_log "[ _change_vm_state ] : Failed to change VM State, Something went wrong..."
                exit 1
            fi
        fi
    else
        _console_log " [ _change_vm_state ] : VM State UnChanged"
    fi
}

# Revert VM Sanpshot by calling manageIQ rest api
_revert_vm_snapshot(){
    revert_snapshot_response=$(_manage_iq 'REVERT_VM_SNAPSHOT')
    _console_log " [ _revert_vm_snapshot ] : Revert Request Message - $revert_snapshot_response"
    sleep 120

}

# Validate VM access by ping and ssh connection check
_validate_vm_access(){

    n=0
    host_ping_status="down"
    ssh_connection_status="not_ok"
    _console_log " [ _validate_vm_access ] Checking 'Host Ping' & 'SSH Connection' Status for the Host : $VM_HOST"

    while [[  ("$n" -lt 50 ) && ("$host_ping_status" != "up" || "$ssh_connection_status" != "ok") ]] ; do
    
        ping -c 1 -W 1 $VM_HOST >> /dev/null 2>&1 
        ping_status=$?
        [ $ping_status -eq 0 ] && host_ping_status="up" || host_ping_status="down"

        nmap_status=$(nmap $VM_HOST -PN -p ssh | egrep '22/tcp open  ssh')

        [ -z "$ssh_connection_status" ] && ssh_connection_status="not_ok" || ssh_connection_status="ok"
    
        _console_log "=>" 1
        n=$(( n + 1 ))
        sleep 10
    done
    _console_log ""
    _console_log " [ _validate_vm_access ] Host Ping Status : $host_ping_status"
    _console_log " [ _validate_vm_access ] SSH Connection Status : $ssh_connection_status"

    if [ "$host_ping_status" != "up" ] || [ "$ssh_connection_status" != "ok" ]
    then
        echo "** [_validate_vm_access] :  Host Unreachable, Something went wrong..."
        exit 1
    fi
}

# Print failure message of exit 1
failure_trap() {
    _console_log " [ FAILED ] : Unable to Provision ManageIQ VM"
}


_validate_input_params(){


    _console_log " [ _validate_input_params ] : Initiated......"


    if [ -z "${VM_NAME}" ] || [ -z "${MIQ_CRED}" ]
    then
        _console_log "[ _validate_input_params ] : ** Please provide valid arguments -h <HOST> & -x <CRED_TOKEN>"
        exit 1
    fi

    manageiq_api_response=$(_manage_iq 'GET_API')
    if [[ $manageiq_api_response == *"unauthorized"* ]]; then
        _console_log " [ _validate_input_params ] : ERROR - Invalid ManageIQ Auth Token, Please check the credentials and retry it again"
        exit 1
    fi

    manageiq_vm_search_result=$(_manage_iq 'GET_VM')
    has_vm_object=$(echo $manageiq_vm_search_result | jq '.resources | length')
    if [[ "$has_vm_object" != "1" ]]; then
        _console_log " [ _validate_input_params ] : ERROR - Unable to find VM, Please verify the given VM Host is belongs to provided manageIQ token account"
        exit 1
    fi
}

trap failure_trap 1


while getopts ":h:x:" opt; do
  case $opt in
    h) VM_HOST="$OPTARG"
    ;;
    x) MIQ_CRED="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

_console_log "Infra Setup Initiated........." 0
_console_log "================================================================================"
_console_log "  VM Host    : ${VM_HOST}"
_console_log "  Datetime   : $(date)"
_console_log "================================================================================"

VM_NAME=$(echo ${VM_HOST%%.*})    
_preload 

if [ -z "${MIQ_VM_ENDPOINT}" ] || [ -z "${MIQ_VM_SNAPSHOT_ENDPOINT}" ]
  then
    echo "** Something went wrong, _preload params are not valid"
    exit 1
fi

_console_log "[2] - Stop VM Initiated : $VM_NAME" 0
_change_vm_state "off" "1"

_console_log "[3] - VM Snapshot Reverte Initiated : $VM_NAME" 0
_revert_vm_snapshot

_console_log "[4] - Start VM Initiated : $VM_NAME" 0
_change_vm_state "on" "1"

_console_log "[5] - Validating VM access : $VM_NAME" 0
_validate_vm_access

_console_log " [ SUCCESS ] : VM Provisoned Successfully" 0

exit 0