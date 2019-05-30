Install openldap pkgs:
  pkg.installed:
    - pkgs:
      - openldap-servers
      - openldap-clients

Install certs:
  pkg.installed:
    - sources:
      - stx-s3-certs: /opt/seagate/stx-s3-certs-1.0-1_s3dev.x86_64.rpm
      - stx-s3-client-certs: /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

slapd:
  service.running:
    - enable: True
