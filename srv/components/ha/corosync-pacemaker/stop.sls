Stop pcs cluster:
  cmd.run:
    - name: pcs cluster stop --force

Stop pcsd:
  service.dead:
    - name: pcsd
    - enable: True
