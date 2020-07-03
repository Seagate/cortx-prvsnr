Start openldap service:
  service.dead:
    - name: slapd
    - enable: False
