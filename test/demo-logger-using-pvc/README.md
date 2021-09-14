# Containerized-Distributed-Logger 📝
Logging Service to demonstrate the distributed logging with log collector.
***

### ⚽ Current Functionality:
  - logger.py periodically logs the demo statements at /var/log/demoLogger
    in the container which automatically gets copied to the /var/log/demoLogger
    file on the node using PV and PVC. ([EOS-24413](https://jts.seagate.com/browse/EOS-24413))

### 🥅 Next Things to Acheive:
  - Deploy glusterfs to have a replicated/distributed log file system. ([EOS-24410](https://jts.seagate.com/browse/EOS-24410))
  - Implement a log collector to gather all the log and bundle them. ([EOS-24417](https://jts.seagate.com/browse/EOS-24417))
***

### 💻 Quick Start:
  - Pre Requisites:
    - Docker and Kubernetes is installed.
    - kubernetes or docker cluster is up & running
  - Commands to deploy:\
    **🤵 On Master Node:**
    - Clone the repository on local machine.
      ```bash
      git clone https://github.com/sumedhak27/Containerized-Distributed-Logger.git
      cd Containerized-Distributed-Logger
      ```
    - Build logger app image, version_num/tag of the image and mentioned in the deployment.yaml should be same.
      ```bash
      docker build -f Dockerfile -t demo-logger:<tag> <path to Dockerfile>
      ```
    - Create Persistent Volume
      ```bash
      kubectl apply -f pv.yaml
      # verify
      kubectl get pv
      ```
    - Create a Persistent Volume Claim
      ```bash
      kubectl apply -f pv-claim.yaml
      # verify
      kubectl get pvc
      ```
    - Create the deployment
      ```bash
      kubectl apply -f deployment.yaml
      # verify Deployment, ReplicaSet & PODS status
      kubectl get all 
      ```
    **👨‍👨‍👦‍👦 On worker nodes:**
    - Check if the logs are generated
      ```bash
      less /var/log/demoLogger/<container_name>.log
      ```
