ntp_packages:
  pkg.installed:
  - name: ntp

ntp_service:
  service.running:
  - enable: true
  - name: {{ server.service }}
  - watch:
    - file: /etc/ntp.conf