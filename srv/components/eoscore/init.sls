{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.eoscore'.format(grains['id'])) %}
include:
  - components.eoscore.prepare
  - components.eoscore.install
  - components.eoscore.config
  # - components.eoscore.start
  - components.eoscore.sanity_check

Generate eoscore checkpoint flag:
  file.managed:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.eoscore
    - makedirs: True
    - create: True

{%- else -%}

EOSCore already applied:
  test.show_notification:
    - text: "Storage states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.eoscore.teardown' to reprovision these states."

{%- endif %}
