Start pcsd:
  service.running:
    - name: pcsd
    - enable: True

Start corosync:
  service.running:
    - name: corosync
    - enable: True

Start pacemaker:
  service.running:
    - name: pacemaker
    - enable: True
