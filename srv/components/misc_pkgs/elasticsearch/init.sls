{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.elasticsearch'.format(grains['id'])) %}
include:
  - components.misc_pkgs.elasticsearch.prepare
  - components.misc_pkgs.elasticsearch.install
  - components.misc_pkgs.elasticsearch.config
  - components.misc_pkgs.elasticsearch.start
  - components.misc_pkgs.elasticsearch.housekeeping
  - components.misc_pkgs.elasticsearch.sanity_check

Generate ElasticSearch checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.elasticsearch
    - makedirs: True
    - create: True
{%- else -%}
ElasticSearch already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.elasticsearch.teardown' to reprovision these states."
{% endif %}