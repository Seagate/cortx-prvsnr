Install elasticsearch:
  pkg.installed:
    - name: elasticsearch
    - version: {{ pillar['commons']['version']['elasticsearch'] }}

# Install elasticsearch:
#   pkg.installed:
#     - sources:
#       - elasticsearch: https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.3.2-x86_64.rpm
