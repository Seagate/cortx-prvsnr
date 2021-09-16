cortx-support-bundle-inside-container 📝
Service to generate a support bundle of Cortx logs in a containerised env.
***

## ⚽ Current Functionality
    - sb_interface.py provides an interface for user to request the support-bundle generation.
      it will deploy a pod which will be responsible to generate support-bundle and will write 
      the tarfile at path: /opt/ using PV & PVC

### 💻 Quick Start
    - Pre Requisites:
      - Docker and Kubernetes is installed.
      - kubernetes or docker cluster is up & running
    - Commands 
      - Create Persistent Volume and Persistent Volume Claim
        ```bash
        ./deploy_pvc.sh
        # verify
        kubectl get pv
        kubectl get pvc
        ```
      - User request to generate support-bundle
        ```bash
        python3 sb_interface.py --generate
        # output
        # Support Bundle generated successfully at path:'/opt/support_bundle.tar.gz' !!!
        ```
      - To read the support-bundle tarfile
        ```bash
        python3 sb_interface.py --untar
        # output
        # Interface will untar the cortx-logs files
        ```
