Stop pcs cluster:
  cmd.run:
    - pcs cluster stop


Stop pcsd:
  service.dead:
    - name: pcsd
    - enable: True


Stop corosync:
  service.dead:
    - name: corosync
    - enable: True


Stop pacemaker:
  service.dead:
    - name: pacemaker

