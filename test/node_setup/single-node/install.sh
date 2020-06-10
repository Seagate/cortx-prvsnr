#!/bin/bash - 
##======================================================================
# This script is meant for quick & easy install via:
#   $ sh install.sh
#========================================================================      
#	title           	: install.sh
#	description     	: This script will install single node cluster on provided machine.
#	author		 		: RE
#	date            	: 20200210
#	version         	: 0.1   
#	usage		 		: bash install.sh -build {BUILD_ID}
#    						-b  = Build ID
#	bash_version    	: 4.2.46(2)-release
#=========================================================================

# Set Build Log Path /tmp/seaget/log
LOG_PATH="/tmp/seaget/log"
LOGFILE="${LOG_PATH}/single_prvnsr.log"
RESULTLOG="${LOG_PATH}/result.log"
RELEASE_NOTES="${LOG_PATH}/RELEASE_NOTES.log"

mkdir -p ${LOG_PATH}
touch ${RELEASE_NOTES}

deploy_single(){
    
    BUILD=$1

    if [[ $BUILD == ees* ]] || [[ $BUILD == eos* ]] || [[ $BUILD == nightly* ]]
    then
        TARGET_BUILD="${BUILD}"
    else
        TARGET_BUILD="integration/centos-7.7.1908/${BUILD}"
    fi

    DEFAULT_REPO="http://ci-storage.mero.colo.seagate.com/releases/eos" 
    REPO="${DEFAULT_REPO}/${TARGET_BUILD}"
    RELEASE_NOTES_URL="${REPO}/RELEASE_NOTES.txt"
    HOST=`hostname`

    echo "================================================================================"
    echo "  Target Build  : ${TARGET_BUILD}"
    echo "  Repository    : ${REPO}"
    echo "  Host Name     : ${HOST}" 
    echo "================================================================================"

    wget http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/prvsnr_uploads/auto-deploy-eos-vm.sh
    sh auto-deploy-eos-vm.sh -S -t ${REPO}
}

validate(){
    STEP=$1
    echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
    if grep -iEq "Result: False|ERROR:|\[ERROR   \]" "${LOGFILE}"
    then
        echo " *** [ $STEP ] EXECUTION STATUS : FAILED" 2>&1 | tee -a "${RESULTLOG}"
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
    elif [[ "$(validate_stack "$1")"  == "1" ]];
    then
        echo " *** [ $STEP ] EXECUTION STATUS : FAILED" 2>&1 | tee -a "${RESULTLOG}"
        echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
        echo "FAILURE CAUSE:" 2>&1 | tee -a "${RESULTLOG}"
        echo "  ERROR : $STEP - Basic Checks are failed" 2>&1 | tee -a "${RESULTLOG}"
        echo "=============================================================<END" 2>&1 | tee -a "${RESULTLOG}"
        exit 0
    else
        echo " *** [ $STEP ] EXECUTION STATUS : SUCCESS" 2>&1 | tee -a "${RESULTLOG}"
    fi
}

validate_stack(){

    STACK_NAME=$1
    STATUS=1
    case $STACK_NAME in
        DEPLOY_SINGLE) if grep -iEq "\[ DEPLOY_SINGLE_NODE_STATUS : SUCCESS \]" "${LOGFILE}"; then STATUS=0 ; fi ;;
    esac
    echo $STATUS
}


cleanup() {
    sed  -i 's/\x1b\[[0-9;]*m//g' "${LOGFILE}"
    sed  -i 's/\x1b\[[0-9;]*m//g' "${RESULTLOG}"
}

trap cleanup  0 1

while getopts ":b:" opt; do
  case $opt in
    b) BUILD="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

# Validate Input
if [ -z "$BUILD" ]
  then
    echo "Invalid execution... Please provide valid argument"
    exit 1
fi


# 1.DEPLOY_SINGLE_NODE
echo "================================================================================"
echo "1. Deploy Cortx on Single Node"
echo "================================================================================"
deploy_single $BUILD 2>&1 | tee -a "${LOGFILE}"
validate 'DEPLOY_SINGLE'

touch "${LOG_PATH}/success"