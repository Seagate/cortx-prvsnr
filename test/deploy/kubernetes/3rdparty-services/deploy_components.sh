#!/bin/bash

namespace="default"
storage_class=${1:-'local-path'}

num_worker_nodes=0
while IFS= read -r line; do
    if [[ $line != *"AGE"* ]]
    then
        IFS=" " read -r -a node_name <<< "$line"
        openldap_worker_node_list[num_worker_nodes]=$node_name
        num_worker_nodes=$((num_worker_nodes+1))
    fi
done <<< "$(kubectl get nodes)"
printf "Number of worker nodes detected: $num_worker_nodes\n"

printf "##########################################################\n"
printf "# Deploying CORTX 3rd party                                  \n"
printf "##########################################################\n"

printf "######################################################\n"
printf "# Deploy Consul                                       \n"
printf "######################################################\n"

# Add the HashiCorp Helm Repository:
helm repo add hashicorp https://helm.releases.hashicorp.com
if [[ $storage_class == "local-path" ]]
then
    printf "Install Rancher Local Path Provisioner"
    kubectl create -f 3rdparty-services/component-packages/local_path_storage.yaml
fi

helm install "consul" hashicorp/consul \
    --set global.name="consul" \
    --set server.storageClass=$storage_class \
    --set server.replicas=$num_worker_nodes \
    --set server.port=8381

printf "######################################################\n"
printf "# Deploy Zookeeper                                    \n"
printf "######################################################\n"
# Add Zookeeper and Kafka Repository
helm repo add bitnami https://charts.bitnami.com/bitnami

helm install zookeeper bitnami/zookeeper \
    --set replicaCount=$num_worker_nodes \
    --set auth.enabled=false \
    --set allowAnonymousLogin=true \
    --set global.storageClass=$storage_class

printf "######################################################\n"
printf "# Deploy Kafka                                        \n"
printf "######################################################\n"
helm install kafka bitnami/kafka \
    --set zookeeper.enabled=false \
    --set replicaCount=$num_worker_nodes \
    --set externalZookeeper.servers=zookeeper.default.svc.cluster.local \
    --set global.storageClass=$storage_class \
    --set defaultReplicationFactor=$num_worker_nodes \
    --set offsetTopicReplicationFactor=$num_worker_nodes \
    --set transactionStateLogReplicationFactor=$num_worker_nodes \
    --set auth.enabled=false \
    --set allowAnonymousLogin=true \
    --set deleteTopicEnable=true \
    --set transactionStateLogMinIsr=2

printf "######################################################\n"
printf "# Deploy OpenLdap                                     \n"
printf "######################################################\n"
kubectl apply -f 3rdparty-services/component-packages/symas_openldap.yaml   

printf "\nWait for CORTX 3rd party to be ready"
while true; do
    count=0
    while IFS= read -r line; do
        IFS=" " read -r -a pod_status <<< "$line"        
        IFS="/" read -r -a ready_status <<< "${pod_status[2]}"
        if [[ "${pod_status[3]}" != "Running" || "${ready_status[0]}" != "${ready_status[1]}" ]]; then
            count=$((count+1))
            break
        fi
    done <<< "$(kubectl get pods -A | grep 'consul\|kafka\|zookeeper\|openldap')"

    if [[ $count -eq 0 ]]; then
        break
    else
        printf "."
    fi    
    sleep 1s
done
printf "\n\n"
