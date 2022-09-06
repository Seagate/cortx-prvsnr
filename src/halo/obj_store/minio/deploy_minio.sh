#!/bin/bash

HOST_FILE=$PWD/hosts
ALL_NODES=$(cat "$HOST_FILE" | awk -F[,] '{print $1}' | cut -d'=' -f2)

(
  set -x; cd "$(mktemp -d)" &&
  OS="$(uname | tr '[:upper:]' '[:lower:]')" &&
  ARCH="$(uname -m | sed -e 's/x86_64/amd64/' -e 's/\(arm\)\(64\)\?.*/\1\2/' -e 's/aarch64$/arm64/')" &&
  KREW="krew-${OS}_${ARCH}" &&
  curl -fsSLO "https://github.com/kubernetes-sigs/krew/releases/latest/download/${KREW}.tar.gz" &&
  tar zxvf "${KREW}.tar.gz" &&
  ./"${KREW}" install krew
)
export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"
# You can skip below if you have run earlier while installing directpv
echo "export PATH=\"\${KREW_ROOT:-$HOME/.krew}/bin:\$PATH\"" >> /root/.bash_profile
source /root/.bash_profile
# Run kubectl krew version to check installation
kubectl krew version

# Install kubectl directpv plugin
kubectl krew install directpv

# Use the plugin to install directpv in your kubernetes cluster
kubectl directpv install

# Wait until directpv has successfully started
sleep 15;

# List available drives in your cluster
kubectl directpv drives ls

# Select drives that directpv should manage and format
for node in "$ALL_NODES"
    do
        kubectl directpv drives format --drives /dev/sd{b...i} --nodes $node
    done

# the update the local copy of plugin index.
kubectl krew update
# install MinIO
kubectl krew install minio
# verify installation
kubectl minio version

kubectl minio init
kubectl get pods -n minio-operator

# Wait until minio Pods are in running state
sleep 40;
