Install Kibana:
  pkg.installed:
    - name: kibana

{% if (grains['os_family'] and ('7.3.2-1' in salt['pkg_resource.version']('kibana'))) %}
Downgrade elasticsearch to 6.8.8:
  cmd.run:
    - name: yum downgrade -y kibana
{% endif %}

# Install Kibana:
#   pkg.installed:
#     - sources:
#       - kibana: https://artifacts.elastic.co/downloads/kibana/kibana-7.3.2-x86_64.rpm
