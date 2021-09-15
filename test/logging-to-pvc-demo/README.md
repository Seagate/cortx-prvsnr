# Containerized-Distributed-Logger 📝

Logging Service to demonstrate the distributed logging with log collector.
***

## ⚽ Current Functionality

  - logger.py periodically logs the sample logs in /var/log/demo-logger/ directory
    per container instance which automatically gets copied to the /var/log/demo-logger/
    directory present on the node using PV and PVC.

## 🥅 Next Things to Acheive

  - Implement Log rotation.
  - Implement a log collector to gather all the log and bundle them.

***

## 💻 Quick Start

  - Pre Requisites:
    - Docker and Kubernetes is installed.
    - kubernetes or docker cluster is up & running

  - Commands to deploy:\
    **🤵 On Master Node:**
      - Clone the repository on local machine.

        ```bash
        git clone https://github.com/Seagate/cortx-prvsnr.git -b kubernetes
        cd cortx-prvsnr/test/logging-to-pvc-demo
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
        less /var/log/demo-logger/<container_name>.log
        ```
