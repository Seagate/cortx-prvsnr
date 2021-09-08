#!/bin/bash -x

kubectl delete pod cortx-data
kubectl delete pvc cortx-config-pvc
kubectl delete pv cortx-config-pv
kubectl delete cm cortx-config
