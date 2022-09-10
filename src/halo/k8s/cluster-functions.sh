#!/bin/bash
#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

source /opt/seagate/halo/k8s/functions.sh

CALICO_PLUGIN_VERSION=v3.23.0
K8_VERSION=1.22.6
DOCKER_VERSION=20.10.8
OS_VERSION=( "CentOS 7.9.2009" "Rocky 8.4" )
export Exception=100
export ConfigException=101

function usage() {
    cat << HEREDOC
Usage : $0 [--prepare, --primary]
where,
    --cleanup - Remove kubernetes and docker related packages on the nodes.
    --prepare - Install prerequisites on nodes for kubernetes setup.
    --status - Print cluster status.
    --primary - Initialize K8 primary node. 
    --join-worker-nodes Join worker nodes to kubernetes cluster.
HEREDOC
}

ACTION="$1"
if [ -z "$ACTION" ]; then
    echo "ERROR : No option provided"
    usage
    exit 1
fi

# try-catch functions
function try() {
    [[ $- = *e* ]]; SAVED_OPT_E=$?
    set +e
}

function throw() {
    exit "$1"
}

function catch() {
    export ex_code=$?
    (( $SAVED_OPT_E )) && set +e
    return $ex_code
} 

function verify_os() {
    CURRENT_OS=$(cut -d ' ' -f 1,4 < /etc/redhat-release)
    if [[ "${OS_VERSION[@]}" =~ $CURRENT_OS ]]; then
        echo "SUCCESS : $CURRENT_OS from allowed OS list"
    else
        echo "ERROR : Operating System is not correct. Current OS : $CURRENT_OS, Required OS should be one of : ${OS_VERSION[*]}"
    fi
}

function print_cluster_status() {
    add_secondary_separator "Node Status"
    SECONDS=0
    while [[ SECONDS -lt 600 ]] ; do
    if ! kubectl get nodes --no-headers | awk '{print $2}' | tr '\n' ' ' | grep -q NotReady ;then
       kubectl get nodes -o wide
       add_secondary_separator "POD Status"
       SECONDS=0
	    while [[ SECONDS -lt 600 ]] ; do
	    if ! kubectl get pods -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}' -A | grep -qi false ; then
	    	kubectl get pods -A -o wide
        	exit 0
	    else
	       add_common_separator "Waiting for pods to become online. Sleeping for 10 sec...."
	       sleep 10
	    fi
	    done
            add_common_separator "PODs are not online within 10mins. Exiting..."
            exit 1
    else
       add_common_separator "Waiting for Nodes to become online. Sleeping for 10 sec...."
       sleep 10
    fi
    done
    add_common_separator "Nodes are not online within 10mins. Exiting..."
    exit 1
}

function cleanup_node() {
    add_secondary_separator "Cleanup Node $HOSTNAME"
    # Cleanup kubeadm stuff
    if [ -f /usr/bin/kubeadm ]; then
        echo "Cleaning up existing kubeadm configuration"
        # Unmount /var/lib/kubelet is having problem while running `kubeadm reset` in k8s v1.19. It is fixed in 1.20
        # Ref link - https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/#kubeadm-reset-unmounts-var-lib-kubelet
        kubeadm reset -f
    fi

    pkgs_to_remove=(
        "docker-ce"
        "docker-ce-cli"
        "containerd"
        "kubernetes-cni"
        "kubeadm"
        "kubectl"
        "python3-pyyaml"
        "jq"
    )
    files_to_remove=(
        "/etc/docker/daemon.json"
        "$HOME/.kube"
        "/etc/systemd/system/docker.service"
        "/etc/cni/net.d"
        "/etc/kubernetes"
        "/var/lib/kubelet"
        "/var/lib/etcd"
        "/var/tmp/solution.yaml"
    )
    services_to_stop=(
        kubelet
        docker
    )
    # Set directive to remove packages with dependencies.
    searchString="clean_requirements_on_remove*"
    conffile="/etc/yum.conf"
    if grep -q "$searchString" "$conffile"
    then
        sed -i "/$searchString/d" "$conffile"
    fi
    echo "clean_requirements_on_remove=1" >> "$conffile"

    # Stopping Services.
    for service_name in ${services_to_stop[@]}; do
        if [ "$(systemctl list-unit-files | grep "$service_name".service -c)" != "0" ]; then
            echo "Stopping $service_name"
            systemctl stop "$service_name".service
        fi
    done

    # Remove packages
    echo "Uninstalling packages"
    yum clean all && rm -rf /var/cache/yum
    for pkg in ${pkgs_to_remove[@]}; do
        if rpm -qa "$pkg"; then
            yum remove "$pkg" -y
            if [ $? -ne 0 ]; then
                echo "Failed to uninstall $pkg"
                exit 1
            fi
        else
            echo -e "\t$pkg is not installed"
        fi
    done
    for file in ${files_to_remove[@]}; do
        if [ -f "$file" ] || [ -d "$file" ]; then
            echo "Removing file/folder $file"
            rm -rf "$file"
        fi
    done
    check_status "Node cleanup failed on $HOSTNAME"
}

function install_prerequisites() {
    add_secondary_separator "Preparing Node $HOSTNAME"
    try
    (
        # Disable swap
        verify_os 
        sudo swapoff -a
        # Keeps the swap off during reboot
        sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

        # Disable selinux
        setenforce 0
        sed -i  -e 's/SELINUX=enforcing/SELINUX=disabled/g' -e 's/SELINUX=enforcing/SELINUX=permissive/g' /etc/sysconfig/selinux || throw $Exception
    
        # Stop and disable firewalld
        (systemctl stop firewalld && systemctl disable firewalld && sudo systemctl mask --now firewalld) || throw $Exception
        # Install python packages
        (yum install python3-pip yum-utils wget jq -y && pip3 install --upgrade pip && pip3 install jq yq) || throw $Exception

        CURRENT_OS=$(cut -d ' ' -f 1,4 < /etc/redhat-release)
        if [ "$CURRENT_OS" == "Rocky 8.4" ]; then
            yum install http://mirror.centos.org/centos/8-stream/AppStream/x86_64/os/Packages/jq-1.6-3.el8.x86_64.rpm -y 
        else
            yum install jq -y     
        fi

        # Set yum repositories for k8 and docker-ce
        rm -rf /etc/yum.repos.d/download.docker.com_linux_centos_7_x86_64_stable_.repo /etc/yum.repos.d/packages.cloud.google.com_yum_repos_kubernetes-el7-x86_64.repo docker-ce.repo
        yum-config-manager --add https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64 || throw $ConfigException
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo || throw $ConfigException     
        yum install kubeadm-$K8_VERSION kubectl-$K8_VERSION kubelet-$K8_VERSION docker-ce-$DOCKER_VERSION --nogpgcheck -y || throw $ConfigException 

        # Setup kernel parameters
        modprobe br_netfilter || throw $ConfigException
        sysctl -w net.bridge.bridge-nf-call-iptables=1 -w net.bridge.bridge-nf-call-ip6tables=1 > /etc/sysctl.d/k8s.conf || throw $ConfigException
        sysctl -p /etc/sysctl.d/k8s.conf || throw $ConfigException

        # Enable cgroupfs 
        sed -i '/config.yaml/s/config.yaml"/config.yaml --cgroup-driver=cgroupfs"/g' /usr/lib/systemd/system/kubelet.service.d/10-kubeadm.conf || throw $ConfigException

        # Enable unix socket
        sed -i 's/fd:\/\//unix:\/\//g' /usr/lib/systemd/system/docker.service && systemctl daemon-reload

        # Enable local docker registry.
        mkdir -p /etc/docker/
        jq -n '{"insecure-registries": $ARGS.positional}' --args "cortx-docker.colo.seagate.com" > /etc/docker/daemon.json || throw $Exception
        echo "Configured /etc/docker/daemon.json for local Harbor docker registry"

        (systemctl start docker && systemctl daemon-reload && systemctl enable docker) || throw $Exception
        echo "Docker Runtime Configured Successfully"

        (systemctl restart kubelet && systemctl daemon-reload && systemctl enable kubelet) || throw $Exception
        echo "kubelet Configured Successfully"


        # Download calico plugin image
        pushd /var/tmp/
            rm -rf calico*.yaml 
            if [ "$CALICO_PLUGIN_VERSION" == "latest" ]; then 
                curl  https://projectcalico.docs.tigera.io/manifests/calico.yaml -o calico-"$CALICO_PLUGIN_VERSION".yaml || throw "$Exception"
            else
                CALICO_PLUGIN_MAJOR_VERSION=$(echo "$CALICO_PLUGIN_VERSION" | awk -F[.] '{print $1"."$2}')
                curl https://projectcalico.docs.tigera.io/archive/"$CALICO_PLUGIN_MAJOR_VERSION"/manifests/calico.yaml -o calico-"$CALICO_PLUGIN_VERSION".yaml || throw "$Exception"
            fi
            CALICO_IMAGE_VERSION=$(grep 'docker.io/calico/cni' calico-"$CALICO_PLUGIN_VERSION".yaml | uniq | awk -F':' '{ print $3}')	
            wget -c https://github.com/projectcalico/calico/releases/download/"$CALICO_IMAGE_VERSION"/release-"$CALICO_IMAGE_VERSION".tgz -O - | tar -xz || throw "$Exception"
            pushd release-"$CALICO_IMAGE_VERSION"/images 
                ls *tar | xargs -I{} docker image load -i {} || throw "$Exception"
            popd
        popd
    )

    catch || {
    # Handle excption
    case "$ex_code" in
        "$Exception")
            echo "An Exception was thrown. Please check logs"
            throw 1
        ;;
        "$ConfigException")
            echo "A ConfigException was thrown. Please check logs"
            throw 1
        ;;
        *)
            echo "An unexpected exception was thrown"
            throw "$ex_code" # you can rethrow the "exception" causing the script to exit if not caught
        ;;
    esac
    }
    check_status "Node preparation failed on $HOSTNAME"
}

function setup_primary_node() {
    local UNTAINT_PRIMARY="$1"
    try
    (
        # Cleanup
        echo "y" | kubeadm reset
        
        # Initialize cluster
        kubeadm init || throw "$Exception"

        # Verify node added in cluster
        # kubectl get nodes || throw $Exception

        # Copy cluster configuration for user
        mkdir -p "$HOME"/.kube
        cp -i /etc/kubernetes/admin.conf "$HOME"/.kube/config
        chown $(id -u):$(id -g) "$HOME"/.kube/config
        # Untaint primary node
        if [ "$UNTAINT_PRIMARY" == "true" ]; then
            add_secondary_separator "Allow POD creation on primary node"
            kubectl taint nodes $(hostname) node-role.kubernetes.io/master- || throw "$Exception"
        fi    

        # Apply calcio plugin 	
        if [ "$CALICO_PLUGIN_VERSION" == "latest" ]; then
            curl https://projectcalico.docs.tigera.io/manifests/calico.yaml -o calico-"$CALICO_PLUGIN_VERSION".yaml || throw "$Exception"
        else
            CALICO_PLUGIN_MAJOR_VERSION=$(echo "$CALICO_PLUGIN_VERSION" | awk -F[.] '{print $1"."$2}')
            curl https://projectcalico.docs.tigera.io/archive/"$CALICO_PLUGIN_MAJOR_VERSION"/manifests/calico.yaml -o calico-"$CALICO_PLUGIN_VERSION".yaml || throw "$Exception"    
        fi

        IS_VM=$(systemd-detect-virt -v)
        if [ "$IS_VM" == "none" ]; then
            # Setup IP_AUTODETECTION_METHOD for determining calico network.
            ITF="$(route -n | awk '$1 == "0.0.0.0" {print $8}' | head -1)"
            sed -i "/# Auto-detect the BGP IP address./i \            - name: IP_AUTODETECTION_METHOD\n              value: 'interface=$ITF'" calico-"$CALICO_PLUGIN_VERSION".yaml
        fi
        kubectl apply -f calico-"$CALICO_PLUGIN_VERSION".yaml || throw "$Exception"

        # Install helm
        curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 || throw "$Exception"
        (chmod 700 get_helm.sh && ./get_helm.sh) || throw "$Exception"
    )

    catch || {
    # Handle excption
    case "$ex_code" in
        $Exception)
            echo "An Exception was thrown. Please check logs"
            throw 1
        ;;
        "$ConfigException")
            echo "A ConfigException was thrown. Please check logs"
            throw 1
        ;;
        *)
            echo "An unexpected exception was thrown"
            throw "$ex_code" # you can rethrow the "exception" causing the script to exit if not caught
        ;;
    esac
    }    
        
}

function join_worker_nodes() {
    add_secondary_separator "Joining Worker Node $HOSTNAME"
    echo 'y' | kubeadm reset && "${@:2}"
    check_status "Failed to join $HOSTNAME node to cluster"
}

case "$ACTION" in
    --cleanup)
        cleanup_node
    ;;
    --prepare) 
        install_prerequisites
    ;;
    --status) 
        print_cluster_status
    ;;
    --primary)
        setup_primary_node "$2"
    ;;
    --join-worker-nodes)
        join_worker_nodes "$@"
    ;;
    *)
        echo "ERROR : Please provide valid option"
        usage
        exit 1
    ;;    
esac
