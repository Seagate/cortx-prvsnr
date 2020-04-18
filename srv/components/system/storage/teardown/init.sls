include:
  - .base-teardown
  - .tidy-up

Mount default OS swap device:
  cmd.run:
    - name: swapon -a || true

Delete storage checkpoint flag:
  file.absent:
    - name: /opt/seagate/eos-prvsnr/generated_configs/{{ grains['id'] }}.storage
