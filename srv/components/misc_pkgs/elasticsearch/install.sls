Install JDK:
  pkg.installed:
    - name: java-1.8.0-openjdk-headless

Install elasticsearch:
  pkg.installed:
    - name: elasticsearch-oss
    - version: {{ pillar['commons']['version']['elasticsearch-oss'] }}

{#% if (grains['os_family'] and ('7.3.2-1' in salt['pkg_resource.version']('elasticsearch'))) %#}
# Downgrade elasticsearch to 6.8.8:
#   cmd.run:
#     - name: yum downgrade -y elasticsearch
{#% endif %#}

Install rsyslog extras:
  pkg.installed:
    - pkgs:
      - rsyslog-elasticsearch: {{ pillar ['commons']['version']['rsyslog-elasticsearch'] }}
      - rsyslog-mmjsonparse: {{ pillar ['commons']['version']['rsyslog-mmjsonparse'] }}

# Install elasticsearch:
#   pkg.installed:
#     - sources:
#       - elasticsearch: https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.3.2-x86_64.rpm
