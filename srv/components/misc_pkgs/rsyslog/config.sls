include:
  - components.misc_pkgs.rsyslog.install

Load UDP mod:
  file.line:
    - name: /etc/rsyslog.conf
    - content: "$ModLoad imudp"
    - match: "#$ModLoad imudp"
    - mode: replace
    - backup: True
    - require:
      - Install rsyslog service


Set UPD port:
  file.line:
    - name: /etc/rsyslog.conf
    - content: "$UDPServerRun 514"
    - match: "#$UDPServerRun 514"
    - mode: replace
    - require:
      - Install rsyslog service

Load TCP mod:
  file.line:
    - name: /etc/rsyslog.conf
    - content: "$ModLoad imtcp"
    - match: "#$ModLoad imtcp"
    - mode: replace
    - require:
      - Install rsyslog service

Set TCP port:
  file.line:
    - name: /etc/rsyslog.conf
    - content: "$InputTCPServerRun 514"
    - match: "#$InputTCPServerRun 514"
    - mode: replace
    - require:
      - Install rsyslog service
