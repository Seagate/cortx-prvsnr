{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.firewall'.format(grains['id'])) %}
include:
  - .prepare
  - .install
  - .config
  - .sanity_check

# Disable Firewall:
#   service.dead:
#     - name: firewalld
#     - enable: false

Generate sspl checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.firewall
    - makedirs: True
    - create: True
{%- else -%}
Firewall already applied:
  test.show_notification:
    - text: "Firewall states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.firewall.teardown' to reprovision these states."
{%- endif -%}
