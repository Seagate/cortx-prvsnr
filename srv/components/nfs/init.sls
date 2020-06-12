{% if not salt['file.file_exists']('/opt/seagate/eos-prvsnr/generated_configs/{0}.nfs'.format(grains['id'])) %}
include:
  - components.nfs.prepare
  - components.nfs.install
  #- components.nfs.config
  - components.nfs.housekeeping
  #- components.nfs.sanity_check

Generate nfs checkpoint flag:
  file.managed:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.nfs
    - makedirs: True
    - create: True
{%- else -%}
nfs already installed:
  test.show_notification:
    - text: "The nfs states already executed on node: {{ grains['id'] }}. Execute 'salt '*' state.apply components.misc_pkgs.nfs.teardown' to reprovision these states."
{% endif %}
