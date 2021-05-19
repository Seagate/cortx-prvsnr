provisioner:
  common_config:
    confstore_url: "json:///opt/seagate/cortx_configs/provisioner_cluster.json"
  cluster_info:
    pillar_dir: /opt/seagate/cortx/provisioner/pillar/groups/all
    num_of_nodes: 1
  storage:
    controller:
      cli_utility_path: /opt/seagate/cortx/provisioner/srv/components/controller/files/scripts/controller-cli.sh

