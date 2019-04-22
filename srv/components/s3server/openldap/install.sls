install_pkgs:
  pkg.installed:
    - pkgs:
      - openldap-servers
      - openldap-clients

# install_certs:
#   pkg.installed:
#     - sources:
#       - stx-s3-certs-*: /opt/stx-s3-certs-*.rpm
#       - stx-s3-client-certs-*: /opt/stx-s3-client-certs-*.rpm

install_certs:
  pkg.installed:
    - sources:
      - stx-s3-certs: /opt/stx-s3-certs-1.0-1_s3dev.x86_64.rpm
      - stx-s3-client-certs: /opt/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

slapd:
  service.running:
    - enable: True
