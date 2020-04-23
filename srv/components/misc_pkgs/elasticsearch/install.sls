Install JDK:
  pkg.installed:
    - name: java-1.8.0-openjdk-headless

Install elasticsearch:
  pkg.installed:
    - name: elasticsearch
    # - version: {{ pillar['commons']['version']['elasticsearch'] }}

{% if (grains['os_family'] and ('7.3.2-1' in salt['pkg_resource.version']('elasticsearch'))) %}
Downgrade elasticsearch to 6.8.8:
  cmd.run:
    - name: yum downgrade -y elasticsearch
{% endif %}

# Install elasticsearch:
#   pkg.installed:
#     - sources:
#       - elasticsearch: https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.3.2-x86_64.rpm
