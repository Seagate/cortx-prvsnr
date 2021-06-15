# Setting up 3 node K8s cluster using Provisioner

1.  Identify 3 nodes for deployment of K8s infra  

2.  Follow the wiki: [Deploy-VM-Hosted-Repo](https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-VM-Hosted-Repo) until [bootstrap-validation](https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-VM-Hosted-Repo#bootstrap-validation) stage  

3.  Check Salt connectivity on the nodes  
    ```Shell
    salt "*" test.ping
    ```  

4.  Run the following command to deploy Kube with containerd config. (NOTE: Docker is optional)  
    ```Shell
    salt "*" state.apply k8s  
    ```

5.  This would install and setup kubeadm on first node.  
    Note: the join command presented in console and execute it on other nodes to join the nodes.  

The above process is mostly built with reference of: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/  
