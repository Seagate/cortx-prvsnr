# include:
#   - components.system.install.base
#   - components.s3server.openldap.cleanup

install_pkgs:
  pkg.installed:
    - pkgs:
      - openldap-servers
      - openldap-clients
