provisioner:
  common_config:
    confstore_url: "json:///opt/seagate/cortx_configs/provisioner_cluster.json"
  cluster:
    cluster_pillar_path: /opt/seagate/cortx/provisioner/pillar/groups/all/cluster.sls
    nodes: 1
