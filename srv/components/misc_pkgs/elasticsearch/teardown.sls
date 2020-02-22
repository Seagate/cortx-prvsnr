Remove elasticsearch:
  pkg.purged:
    - name: elasticsearch


Remove elasticsearch config:
  file.absent:
    - name: /etc/elasticsearch

Remove elasticsearch data:
  file.absent:
    - name: /var/lib/elasticsearch
