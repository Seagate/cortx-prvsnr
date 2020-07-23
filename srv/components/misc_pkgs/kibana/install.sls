Install Kibana:
  pkg.installed:
    - name: kibana-oss
    - version: {{ pillar['commons']['version']['kibana-oss'] }}

{#% if (grains['os_family'] and ('7.3.2-1' in salt['pkg_resource.version']('kibana'))) %#}
# Downgrade elasticsearch to 6.8.8:
#   cmd.run:
#     - name: yum downgrade -y kibana
{#% endif %#}
