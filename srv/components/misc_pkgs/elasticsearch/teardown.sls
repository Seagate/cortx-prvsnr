Remove elasticsearch:
  pkg.purged:
    - name: elasticsearch


Remove elasticsearch config:
  file.absent:
    - name: /etc/elasticsearch

Remove elasticsearch data:
  file.absent:
    - name: /var/lib/elasticsearch

Delete elasticsearch checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.elasticsearch
