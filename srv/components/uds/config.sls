Add USL native.key file:
  file.managed:
    - source: salt://components/uds/files/tls/native.key
    - name: /var/csm/tls/native.key
    - mode: 600
    - user: csm
    - group: csm

Add USL native.crt file:
  file.managed:
    - source: salt://components/uds/files/tls/native.crt
    - name: /var/csm/tls/native.crt
    - mode: 600
    - user: csm
    - group: csm
