install_pkgs:
  pkg.installed:
    - pkgs:
      - openldap-servers
      - openldap-clients

slapd:
  service.running:
    - enable: True
