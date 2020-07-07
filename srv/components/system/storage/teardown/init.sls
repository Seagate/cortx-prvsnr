include:
  - .base-teardown
{% if "physical" in grains['virtual'] %}
  - .tidy-up
{% endif %}

Mount default OS swap device:
  cmd.run:
    - name: swapon -a || true

Delete storage checkpoint flag:
  file.absent:
    - name: /opt/seagate/cortx/provisioner/generated_configs/{{ grains['id'] }}.storage
