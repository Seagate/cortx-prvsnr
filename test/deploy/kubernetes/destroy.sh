#!/bin/bash -x

kubectl delete pod cortx-provisioner --namespace cortx
kubectl delete pvc cortx-config-pvc --namespace cortx
kubectl delete pv cortx-config-pv --namespace cortx
kubectl delete cm cortx-config --namespace cortx
kubectl delete cm machine-id --namespace cortx
