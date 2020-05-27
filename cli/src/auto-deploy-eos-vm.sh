#!/bin/bash
# Script to run end to end deployment of Cortx for Single and Dual node setup on VM.

set -euE

export LOG_FILE="${LOG_FILE:-/var/log/seagate/provisioner/auto-deploy-eos.log}"
mkdir -p $(dirname "${LOG_FILE}")
# /usr/bin/true > $LOG_FILE
truncate -s 0 ${LOG_FILE}

PRVSNR_ROOT="/opt/seagate/eos-prvsnr"

trap_handler ()
{
    echo -e "\n***** FAILED!!*****" 2>&1 | tee -a $LOG_FILE
    echo "Detailed error log is kept at: $LOG_FILE" 2>&1 | tee -a $LOG_FILE
    exit 1
}
trap trap_handler ERR

srvnode_1_host=`hostname`
srvnode_2_host=
srvnode_2_passwd=
tgt_build=
singlenode=false

srvnode_2_host_opt=false
srvnode_2_passwd_opt=false
tgt_build_opt=false

usage()
{
    echo "\
Usage:
For Dual Node:
auto-deploy-eos { -s <secondary node hostname (srvnode-2)> -p <password for sec node>
                  -t <target build url for EOS>
For Single Node:
auto-deploy-eos { -S -t <target build url for EOS> }
"
}

help()
{
  echo "\
----------- Caveats -------------
1. The command must be run from primary node in the cluster.
2. Ensure the setup is clean and no eos rpms are installed.
3. Ensure the ~/.ssh directory is empty.
-------- Sample command ---------
For Dual Node:
$ auto-deploy-eos -s ssc-vm-c-810.colo.seagate.com -p 'seagate'
  -t http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/2023/
For Single Node:
$ auto-deploy-eos -S -t http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/2023/

"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) usage; help; exit 0
        ;;
        -s)
            srvnode_2_host_opt=true
            [ -z "$2" ] &&
                echo "Error: srvnode-2 not provided" && exit 1;
            srvnode_2_host="$2"
            shift 2 ;;
        -p)
            srvnode_2_passwd_opt=true
            [ -z "$2" ] &&
                echo "Error: srvnode-2 password not provided" && exit 1;
            srvnode_2_passwd="$2"
            shift 2 ;;
        -S)
	        singlenode=true
            shift 1 ;;
        -t)
            tgt_build_opt=true
            [ -z "$2" ] &&
                echo "Error: Target build not provided" && exit 1;
            tgt_build="$2"
            shift 2 ;;
        *) echo "Invalid option $1"; usage; exit 1;;
    esac
done

if [[ "$singlenode" == false ]]; then
    if [[ "$srvnode_2_host_opt" == false ||
          "$srvnode_2_passwd_opt" == false ||
          "$tgt_build_opt" == false ]]; then

	echo "Insufficient input provided"
        usage
        exit 1
    fi
elif [[ "$tgt_build_opt" == false ]]; then
    echo "Insufficient input provided"
    usage
    exit 1
fi

if [[ "$singlenode" == false ]]; then
    ssh_tool="/usr/bin/sshpass"
    ssh_base_cmd="/bin/ssh"
    ssh_opts="-o UserKnownHostsFile=/dev/null\
              -o StrictHostKeyChecking=no -o LogLevel=error"
    user=root
    ssh_cred="$ssh_tool -p $srvnode_2_passwd"
    ssh_cmd="$ssh_base_cmd $ssh_opts $user@$srvnode_2_host"
    remote_cmd="$ssh_cred $ssh_cmd"
	
    ssh_tool_pkg=$(basename $ssh_tool)
    [ -f "$ssh_tool" ] || {
	echo "Installing $ssh_tool_pkg"
	yum install -y $ssh_tool_pkg
	}
fi

install_prvsnr_cli()
{
    # Install eos-prvsnr-cli rpm from ci-storage and install it on both nodes
    target_node="$1"
    echo "Target Node: $target_node" 2>&1|tee -a $LOG_FILE
    if [[ "$target_node" = "srvnode-1" ]]; then
        rpm -qa | grep -q eos && {
            echo "ERROR: eos packages are already installed"
            echo "Please clean-up previous installtion from both the nodes and retry"
            exit 1
        }
	    curl http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/prvsnr_uploads/eos-install-prereqs-vm.sh | bash
		echo "Installing prvsnr-cli on $target_node" 2>&1|tee -a $LOG_FILE
        yum install -y $tgt_build/$(curl -s $tgt_build/|grep eos-prvsnr-cli-1.0.0| sed 's/<\/*[^>]*>//g'|cut -d' ' -f1)
        systemctl stop firewalld || true
        return 0
    else
		echo "Target Node: $target_node" 2>&1|tee -a $LOG_FILE
	
		$remote_cmd <<-EOF
			set -eu
			rpm -qa | grep -q eos && {
			echo "ERROR: eos packages are already installed"
			echo "Please clean-up previous installtion from both the nodes and retry"
			exit 1
			}
			curl http://ci-storage.mero.colo.seagate.com/releases/eos/uploads/prvsnr_uploads/eos-install-prereqs-vm.sh | bash
			echo "Installing prvsnr-cli on $target_node" 2>&1|tee -a $LOG_FILE
			yum install -y $tgt_build/$(curl -s $tgt_build/|grep eos-prvsnr-cli-1.0.0| sed 's/<\/*[^>]*>//g'|cut -d' ' -f1)
			systemctl stop firewalld || true

		EOF
    fi
}

install_config_prvsnr()
{   if [[ "$singlenode" == false ]]; then
		set -eu
		echo -e "\n\t***** INFO: Installing eos-prvsnr-cli on node-2 *****" 2>&1 | tee -a $LOG_FILE
		sleep 1
		install_prvsnr_cli "srvnode-2"
    fi
    echo -e "\n\t***** INFO: Installing eos-prvsnr-cli on node-1*****" 2>&1 | tee -a $LOG_FILE
    sleep 1
    install_prvsnr_cli "srvnode-1"

    # Run setup provisioner
    echo -e "\n\t***** INFO: Running setup-provisioner *****" 2>&1 | tee -a $LOG_FILE
    sleep 1
    if [[ "$singlenode" == false ]]; then
	    echo -e "\n\tRunning sh /opt/seagate/eos-prvsnr/cli/setup-provisioner"\
		        "--srvnode-2='$srvnode_2_host' --repo-src=gitlab VM-fixes" 2>&1 | tee -a $LOG_FILE
	    sh /opt/seagate/eos-prvsnr/cli/setup-provisioner --srvnode-2="$srvnode_2_host" --repo-src=gitlab VM-fixes 2>&1 | tee -a $LOG_FILE
	    echo "Done" 2>&1 | tee -a $LOG_FILE
    else
	    echo -e "\n\tRunning sh /opt/seagate/eos-prvsnr/cli/setup-provisioner"\
	            "-S --salt-master="$srvnode_1_host" --repo-src=gitlab VM-fixes" 2>&1 | tee -a $LOG_FILE
        sh /opt/seagate/eos-prvsnr/cli/setup-provisioner -S --salt-master="$srvnode_1_host" --repo-src=gitlab VM-fixes 2>&1 | tee -a $LOG_FILE
        echo "Done" 2>&1 | tee -a $LOG_FILE
    fi	
}

update_pillar()
{
    # Update cluster.sls
    echo -e "\n\t***** INFO: Updating cluster.sls *****" 2>&1 | tee -a $LOG_FILE

    local _cluster_sls_path=${PRVSNR_ROOT}/pillar/components/cluster.sls
    if [[ -f "${PRVSNR_ROOT}/pillar/user/groups/all/cluster.sls" ]]; then
        _cluster_sls_path=${PRVSNR_ROOT}/pillar/user/groups/all/cluster.sls
    fi
    cp $_cluster_sls_path ${_cluster_sls_path}.org
	
	# Update hostname if singlenode
	if [[ "$singlenode" == false ]]; then
		sed -i "s/hostname: srvnode-1/hostname: ${srvnode_1_host}/g" $_cluster_sls_path
	fi	
	
    # Update Mgmt and data interface
    echo "Update Mgmt and data interface" 2>&1|tee -a $LOG_FILE
    sed -ie "s/eno1/eth0/g" $_cluster_sls_path
    sed -ie "s/enp175s0f0/eth2/g" $_cluster_sls_path
    sed -ie "s/enp175s0f1/eth1/g" $_cluster_sls_path
    
    # Removing pvt_ip_addr and roaming_ip
    echo "Removing pvt_ip_addr and roaming_ip" 2>&1|tee -a $LOG_FILE
    sed -i "s/\(^.*\)\(pvt_ip_addr:\)\(.*\)/\1pvt_ip_addr:/" $_cluster_sls_path
    sed -i "s/\(^.*\)\(roaming_ip:\)\(.*\)/\1roaming_ip:/" $_cluster_sls_path
	
    # Changing Meta and Data disks based on lsblk
    echo "Changing Meta and Data disks based on lsblk" 2>&1|tee -a $LOG_FILE
    disks=$(lsblk | grep -E ^v.*"disk" | cut -c1-3 | sed "1 d")
    meta_disk=0
    for i in $disks
    do
        if [ $meta_disk == 0 ] ; then
            meta_disk=1
			sed -i "s/sdb/${i}/g" $_cluster_sls_path;
		else
			sed -i "s/sdc/${i}/g" $_cluster_sls_path;
		fi
    done
	
    # Update release.sls
    echo -e "\n\t***** INFO: Updating release.sls *****" 2>&1 | tee -a $LOG_FILE
    sed -i "s~VM-fixes~${tgt_build}~" /opt/seagate/eos-prvsnr/pillar/components/release.sls;
	
    # Update s3server.sls
    echo -e "\n\t***** INFO: Updating s3server.sls *****" 2>&1 | tee -a $LOG_FILE
    sed -i "s/no_of_inst: 11\+/no_of_inst: 2/g" /opt/seagate/eos-prvsnr/pillar/components/s3server.sls;
}

install_config_prvsnr
update_pillar

# Run deploy_eos
echo -e "\n\t***** INFO: Running deploy-eos *****"
sleep 5
if [[ "$singlenode" == false ]]; then
    sh /opt/seagate/eos-prvsnr/cli/src/deploy-eos-vm -v
else
    sh /opt/seagate/eos-prvsnr/cli/src/deploy-eos-vm -S
fi
echo -e "\n***** SUCCESS!! *****" 2>&1 | tee -a $LOG_FILE
echo " Check following logs to see the complete logs of auto-deploy-eos: $LOG_FILE" 2>&1 | tee -a $LOG_FILE
echo "Done"
