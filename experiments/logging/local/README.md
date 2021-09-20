# Containerized-Distributed-Logger 📝

Logging Service to demonstrate the distributed logging with log collector.
***

## ⚽ Current Functionality

  - logger.py periodically logs the sample logs in `/var/log/cortx/<app_name>` directory
    per container instance which automatically gets copied to the same
    directory present on the node using PV and PVC.

## 🥅 Next Things to Achieve

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
        cd cortx-prvsnr/experiments/logging/local/
        ```

      - Build logger app image.
        - Deault app_name is `demo-logger`,\
          to change it to `cortx-motr` for example, edit the last line in Dockerfile as follows\
          `ENTRYPOINT ["python3", "/opt/demo-logger/logger.py", "--app-name", "cortx-motr"]`

        - run the command
          ```bash
          docker build -t <app_name>:<tag> <path to Dockerfile>
          ```

        - Update the `image_name:tag` in deployment.yaml as well the default is `demo-logger:1.1`

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
        less /var/log/cortx/<app_name>/<container_name>.log
        ```
