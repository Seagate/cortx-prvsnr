Install openldap pkgs:
  pkg.installed:
    - pkgs:
      - openldap-servers
      - openldap-clients

Update to latest selinux-policy:
  pkg.installed:
    - name: selinux-policy

Enable http port in selinux:
  cmd.run:
    - name: setsebool httpd_can_network_connect true -P
    - onlyif: salt['grains.get']('selinux:enabled')

Install certs:
  pkg.installed:
    - sources:
      - stx-s3-certs: /opt/seagate/stx-s3-certs-1.0-1_s3dev.x86_64.rpm
      - stx-s3-client-certs: /opt/seagate/stx-s3-client-certs-1.0-1_s3dev.x86_64.rpm

set_chkconfig_on:
  cmd.run:
    - name: chkconfig slapd on

slapd:
  service.running:
    - enable: True
    - require:
      - pkg: Install openldap pkgs
      - pkg: Install certs