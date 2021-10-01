#!/bin/bash

namespace="default"
pvc_consul_filter="data-default-consul"
pvc_kafka_filter="kafka"
pvc_zookeeper_filter="zookeeper"
pv_filter="pvc"
openldap_pvc="openldap-data"

#############################################################
# Destroy CORTX 3rd party
#############################################################

printf "###################################\n"
printf "# Delete Kafka                    #\n"
printf "###################################\n"
helm uninstall kafka

printf "###################################\n"
printf "# Delete Zookeeper                #\n"
printf "###################################\n"
helm uninstall zookeeper

printf "###################################\n"
printf "# Delete Consul                   #\n"
printf "###################################\n"
helm delete consul
kubectl delete -f 3rdparty-services/component-packages/local_path_storage.yaml

printf "######################################################\n"
printf "# Delete OpenLdap                                     \n"
printf "######################################################\n"
kubectl delete -f 3rdparty-services/component-packages/symas_openldap.yaml

printf "###################################\n"
printf "# Delete Persistent Volume Claims #\n"
printf "###################################\n"
volume_claims=$(kubectl get pvc --namespace=default | grep -E "$pvc_consul_filter|$pvc_kafka_filter|$pvc_zookeeper_filter|$openldap_pvc" | cut -f1 -d " ")
echo $volume_claims
for volume_claim in $volume_claims
do
    printf "Removing $volume_claim\n"
    kubectl delete pvc $volume_claim
done

if [[ $namespace != 'default' ]]; then
    volume_claims=$(kubectl get pvc --namespace=$namespace | grep -E "$pvc_consul_filter|$pvc_kafka_filter|$pvc_zookeeper_filter|$openldap_pvc" | cut -f1 -d " ")
    echo $volume_claims
    for volume_claim in $volume_claims
    do
        printf "Removing $volume_claim\n"
        kubectl delete pvc $volume_claim
    done
fi

printf "###################################\n"
printf "# Delete Persistent Volumes       #\n"
printf "###################################\n"
persistent_volumes=$(kubectl get pv --namespace=default | grep -E "$pvc_consul_filter|$pvc_kafka_filter|$pvc_zookeeper_filter" | cut -f1 -d " ")
echo $persistent_volumes
for persistent_volume in $persistent_volumes
do
    printf "Removing $persistent_volume\n"
    kubectl delete pv $persistent_volume
done

if [[ $namespace != 'default' ]]; then
    persistent_volumes=$(kubectl get pv --namespace=default | grep -E "$pvc_consul_filter|$pvc_kafka_filter|$pvc_zookeeper_filter" | cut -f1 -d " ")
    echo $persistent_volumes
    for persistent_volume in $persistent_volumes
    do
        printf "Removing $persistent_volume\n"
        kubectl delete pv $persistent_volume
    done
fi

# Delete CORTX namespace
if [[ "$namespace" != "default" ]]; then
    kubectl delete namespace $namespace
fi
