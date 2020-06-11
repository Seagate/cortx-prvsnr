#!/bin/bash - 
##======================================================================
# This script is meant for quick & easy install via:
#   $ sh install.sh
#========================================================================      
#	title           	: install.sh
#	description     	: This script will install dual node cluster on provided machine.
#	author		 		: RE
#	date            	: 20200210
#	version         	: 0.1   
#	usage		 		: bash install.sh -b {BUILD_ID} -s {NODE_1} -c {NODE_2} -p {SSH_PASS} -C {Cluster_ip} -M {mgmt_vip} -i {pvt_data_ip1} -I {pvt_data_ip2}
#    						-b  = Build ID
#                           -s  = Server (NODE 1) HOST
#                           -c  = Client (NODE 2) HOST
#                           -p  = SSH PASS
#                           -C  = Cluster PVT_IP
#                           -M  = Mgmt VIP
#                           -i  = pvt_data_ip1
#                           -I  = pvt_data_ip2
#	bash_version    	: 4.2.46(2)-release
#   ref                 : http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr/wikis/Setup-Guides/QuickStart-Guide
#=========================================================================

_pre_process(){

    LOG_PATH="/tmp/seaget/log"
    LOGFILE="${LOG_PATH}/deploy_dual.log"
    RESULTLOG="${LOG_PATH}/result.log"
    MANIFEST_FILE="${LOG_PATH}/MANIFEST.log"

    mkdir -p ${LOG_PATH}
    touch ${MANIFEST_FILE}

    yum install -y yum-utils wget expect sshpass;
    wget -O "${MANIFEST_FILE}" "${REPO}/MANIFEST.MF"
}

_deploy_dual(){
    
    BUILD=$1
    NODE1_HOST=$2
    NODE2_HOST=$3
    SSH_PASS=$4
    CLUSTER_IP=$5
    MGMT_VIP=$6
    PVT_IP1=$7
    PVT_IP2=$8

    # 1. Validation
    if [[ $BUILD == ees* ]] || [[ $BUILD == eos* ]] || [[ $BUILD == nightly* ]]
    then
        TARGET_BUILD="${BUILD}"
    else
        TARGET_BUILD="integration/centos-7.7.1908/${BUILD}"
    fi

    # 2. Install Reference
    DEFAULT_REPO="http://ci-storage.mero.colo.seagate.com/releases/eos" 
    REPO="${DEFAULT_REPO}/${TARGET_BUILD}"

    echo "================================================================================"
    echo "  Target Build  : ${TARGET_BUILD}"
    echo "  Repository    : ${REPO}"
    echo "  Node 1 Host   : ${NODE1_HOST}" 
    echo "  Node 2 Host   : ${NODE2_HOST}"
    if [ $CLUSTER_IP -ne 'null' ]; then
        echo "  CLUSTER_IP : ${CLUSTER_IP}"
    fi
    if [ $MGMT_VIP -ne 'null' ]; then
        echo "  MGMT_VIP : ${MGMT_VIP}"
    fi
    if [ $PVT_IP1 -ne 'null' ]; then
        echo "  PVT_IP for Host1: ${PVT_IP1}"
    fi
    if [ $PVT_IP2 -ne 'null' ]; then
        echo "  PVT_IP for Host2: ${PVT_IP2}"
    fi
    echo "================================================================================"

    wget http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/prvsnr_uploads/auto-deploy-eos-vm.sh
    if [ $CLUSTER_IP -ne 'null' && $MGMT_VIP -ne 'null' && $PVT_IP1 -ne 'null' && $PVT_IP2 -ne 'null' ]; then
        sh auto-deploy-eos-vm.sh -s ${NODE2_HOST} -p ${SSH_PASS} -C ${CLUSTER_IP} -M ${MGMT_VIP} -i ${PVT_IP1} -I ${PVT_IP2} -t ${REPO}
    elif [ $CLUSTER_IP -ne 'null' && $MGMT_VIP -ne 'null' && $PVT_IP1 == 'null' && $PVT_IP2 == 'null']; then
        sh auto-deploy-eos-vm.sh -s ${NODE2_HOST} -p ${SSH_PASS} -C ${CLUSTER_IP} -M ${MGMT_VIP} -t ${REPO}
    elif [ $CLUSTER_IP == 'null' && $MGMT_VIP == 'null' && $PVT_IP1 != 'null' && $PVT_IP2 != 'null']; then
        sh auto-deploy-eos-vm.sh -s ${NODE2_HOST} -p ${SSH_PASS} -i ${PVT_IP1} -I ${PVT_IP2} -t ${REPO}
    else
        sh auto-deploy-eos-vm.sh -s ${NODE2_HOST} -p ${SSH_PASS} -t ${REPO}
    fi
    echo " [ _deploy_dual ] : Cortx deploy for Dual node is completed" 
}

_check_for_errors_in_log(){
    STACK_NAME=$1
    echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
    if grep -iEq "Result: False|\[ERROR   \]" "${LOGFILE}"
    then
        echo " *** [ $STACK_NAME ] EXECUTION STATUS : FAILED" 2>&1 | tee -a "${RESULTLOG}"
        echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
        echo "FAILURE CAUSE:" 2>&1 | tee -a "${RESULTLOG}"

        if grep -iEq "Result: False" "${LOGFILE}"
        then
            grep -B 4 -A 3 "Result: False" "${LOGFILE}" 2>&1 | tee -a "${RESULTLOG}"
        fi
        
        if grep -iEq "ERROR:" "${LOGFILE}"  
        then
            grep  -B 1 -A 2 "ERROR:" "${LOGFILE}"  2>&1 | tee -a "${RESULTLOG}"
        fi
        
        if grep -iEq "\[ERROR   \]" "${LOGFILE}"
        then
            grep -B 1 -A 3 "\[ERROR   \]" "${LOGFILE}" 2>&1 | tee -a "${RESULTLOG}"
        fi
        echo "==========================================================<<END" 2>&1 | tee -a "${RESULTLOG}"
        exit 0
    fi
}

_validate_stack(){

    STACK_NAME=$1
    STATUS=1
    case $STACK_NAME in
        DEPLOY_DUAL) 
            if grep -iEq "NODE 1 STATUS - SUCCESS" "${LOGFILE}" && grep -iEq "NODE 2 STATUS - SUCCESS" "${LOGFILE}"; then
                _check_for_errors_in_log $STACK_NAME
                STATUS=0 ;
            fi 
        ;;
    esac

    if [[ "$STATUS"  == "1" ]];
    then
        echo " *** [ $STACK_NAME ] EXECUTION STATUS : FAILED" 2>&1 | tee -a "${RESULTLOG}"
        echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
        echo "FAILURE CAUSE:" 2>&1 | tee -a "${RESULTLOG}"
        echo "ERROR : $STACK_NAME - BASIC CHECKS ARE FAILED" 2>&1 | tee -a "${RESULTLOG}"
        echo "=============================================================<END" 2>&1 | tee -a "${RESULTLOG}"
        exit 0
    else
        echo " *** [ $STACK_NAME ] EXECUTION STATUS : SUCCESS" 2>&1 | tee -a "${RESULTLOG}"
    fi

    echo $STATUS
}

_cleanup() {
    sed  -i 's/\x1b\[[0-9;]*m//g' "${LOGFILE}"
    sed  -i 's/\x1b\[[0-9;]*m//g' "${RESULTLOG}"
}

trap _cleanup 0 1

while getopts ":b:s:c:p:" opt; do
  case $opt in
    b) BUILD="$OPTARG"
    ;;
    s) NODE1_HOST="$OPTARG"
    ;;
    c) NODE2_HOST="$OPTARG"
    ;;
    p) SSH_PASS="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

# _validate_stack Input
if [ -z "$BUILD" ] || [ -z "$NODE1_HOST" ] || [ -z "$NODE2_HOST" ] || [ -z "$SSH_PASS" ] 
  then
    echo "Invalid execution... Please provide valid argument"
    exit 0
fi

_pre_process

# 1.Deploy Cortx on Dual node
echo "================================================================================"
echo "1. Deploy Cortx on Dual node"
echo "================================================================================"
_deploy_dual $BUILD $NODE1_HOST $NODE2_HOST $SSH_PASS 2>&1 | tee -a "${LOGFILE}"
_validate_stack 'DEPLOY_DUAL'

touch "${LOG_PATH}/success"